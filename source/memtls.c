/*
 * memtls.c -- implicit Thread Local Storage support for MemoryModule.
 *
 * See memtls.h and docs/tls-memorymodule-plan.md for the design. In short: a
 * hand-mapped PE that uses `__declspec(thread)` data needs the loader to
 * allocate a TLS index, extend every thread's ThreadLocalStoragePointer and
 * register the module so future threads are served too. There is no public API
 * for this; the only correct, future-thread-safe way is to call the real
 * (unexported) ntdll!LdrpHandleTlsData with a synthetic LDR_DATA_TABLE_ENTRY.
 *
 * This module:
 *   1. locates ntdll!LdrpHandleTlsData by scanning ntdll's .text for a
 *      version-gated prologue signature (see g_patterns),
 *   2. validates the candidate with a behavioural self-test using a tiny
 *      synthetic in-memory image carrying one __declspec(thread)-style slot,
 *      so a mis-identified address fails loudly instead of corrupting state,
 *   3. caches the validated function pointer and calls it for real modules.
 *
 * Distributed under the same MIT/X11 OR (MPL 2.0) terms as the rest of py2exe.
 */

#include <windows.h>
#include <winternl.h>
#include <intrin.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>

#include "memtls.h"

#ifndef IMAGE_DIRECTORY_ENTRY_TLS
#define IMAGE_DIRECTORY_ENTRY_TLS 9
#endif

#ifndef NT_SUCCESS
#define NT_SUCCESS(Status) (((NTSTATUS)(Status)) >= 0)
#endif

/* ---- logging ---------------------------------------------------------- */
/*
 * Gated on PY2EXE_VERBOSE (same knob the rest of the runtime uses, see
 * CLAUDE.md). Reads the env var once and prints to stderr.
 */
static int tls_verbose(void)
{
    static int level = -1;
    if (level == -1) {
        const char *v = getenv("PY2EXE_VERBOSE");
        level = v ? atoi(v) : 0;
    }
    return level;
}

static void tls_log(const char *fmt, ...)
{
    va_list ap;
    if (tls_verbose() <= 0)
        return;
    va_start(ap, fmt);
    fputs("py2exe[memtls]: ", stderr);
    vfprintf(stderr, fmt, ap);
    fputc('\n', stderr);
    va_end(ap);
}

/* ---- LdrpHandleTlsData function pointer typedef ----------------------- */
/*
 * On x64 the single argument is passed in RCX (the only convention).
 * On win32 the convention is thiscall on Windows 8.1+ (the argument is passed
 * in ECX, callee cleans the stack) -- this is binary-compatible with a
 * __fastcall function whose first argument lands in ECX and which takes no
 * stack arguments, so we model it with __fastcall and a dummy EDX argument.
 * (Pre-8.1 stdcall builds are out of the supported range; see the plan.)
 */
#ifdef _WIN64
typedef NTSTATUS(NTAPI *LdrpHandleTlsData_t)(PVOID Entry);
#define CALL_LDRP(fn, entry) ((fn)(entry))
#else
typedef NTSTATUS(__fastcall *LdrpHandleTlsData_t)(PVOID Entry, PVOID Edx);
#define CALL_LDRP(fn, entry) ((fn)((entry), NULL))
#endif

/*
 * Synthetic LDR_DATA_TABLE_ENTRY. LdrpHandleTlsData only needs DllBase (read
 * from a fixed offset: 0x30 on x64, 0x18 on x86 -- the head of the structure
 * has been stable for decades) and writes a couple of fields back (TlsIndex).
 * We oversize the structure well beyond any real LDR_DATA_TABLE_ENTRY and zero
 * it, so every field ntdll touches lands inside our buffer. It is allocated
 * once per module and intentionally never freed: ntdll keeps a reference to it
 * in its global LdrpTlsList for the lifetime of the process.
 */
#ifdef _WIN64
#define LDR_DLLBASE_OFFSET 0x30
#else
#define LDR_DLLBASE_OFFSET 0x18
#endif

typedef struct {
    unsigned char head[LDR_DLLBASE_OFFSET];
    PVOID DllBase;
    unsigned char tail[0x300];
} SYNTH_LDR_ENTRY;

/* ---- loader lock (exported from ntdll) -------------------------------- */
typedef NTSTATUS(NTAPI *LdrLockLoaderLock_t)(ULONG Flags, ULONG *State, ULONG_PTR *Cookie);
typedef NTSTATUS(NTAPI *LdrUnlockLoaderLock_t)(ULONG Flags, ULONG_PTR Cookie);

/* ---- ntdll .text discovery -------------------------------------------- */
static BOOL get_ntdll_text(unsigned char **base_out,
                           unsigned char **text_out, size_t *size_out)
{
    unsigned char *base = (unsigned char *)GetModuleHandleW(L"ntdll.dll");
    PIMAGE_DOS_HEADER dos;
    PIMAGE_NT_HEADERS nt;
    PIMAGE_SECTION_HEADER sec;
    WORD i;

    if (!base)
        return FALSE;
    dos = (PIMAGE_DOS_HEADER)base;
    if (dos->e_magic != IMAGE_DOS_SIGNATURE)
        return FALSE;
    nt = (PIMAGE_NT_HEADERS)(base + dos->e_lfanew);
    if (nt->Signature != IMAGE_NT_SIGNATURE)
        return FALSE;

    sec = IMAGE_FIRST_SECTION(nt);
    for (i = 0; i < nt->FileHeader.NumberOfSections; i++, sec++) {
        if (memcmp(sec->Name, ".text", 5) == 0) {
            *base_out = base;
            *text_out = base + sec->VirtualAddress;
            *size_out = sec->Misc.VirtualSize ? sec->Misc.VirtualSize
                                              : sec->SizeOfRawData;
            return TRUE;
        }
    }
    return FALSE;
}

/* ---- signature: entry prologue + body anchor -------------------------- *
 *
 * Locating LdrpHandleTlsData by its prologue alone is unreliable: the
 * compiler-generated register-save prologue is short and not unique (the same
 * push/mov sequence appears in many ntdll functions, and the exact saved
 * registers differ per build). Instead we use two patterns:
 *
 *   - `entry`  matches the *start* of the function (so a match IS the entry
 *              address), kept to the bytes common to every observed build;
 *   - `anchor` is a distinctive sequence from the function *body* (the
 *              algorithm itself, not the prologue) that must appear within
 *              `window` bytes of the entry to confirm the candidate.
 *
 * Keying the confirmation on the body makes one signature span many builds:
 * the body anchor is the same logic Blackbone keys on (the `lea r8d,[rbx+9]`
 * LoadReason check on x64), but we wildcard the volatile bytes so a single
 * pattern covers Win10 1809 .. Win11 23H2 instead of one per build.
 * 0xFF in a mask byte means "must match"; 0x00 is a wildcard. A stale
 * signature still fails loudly via the self-test rather than misbehaving.
 *
 * Verified against ntdll from: Win10 1809 (17763), Win10 2004-22H2 (19042),
 * Server 2022 / CI (20348), Win11 22H2/23H2 (22621). The x86 anchor is
 * verified on 22621 (and is Blackbone's Win11 x86 signature); x86 is
 * build-only in CI, so other x86 builds rely on the runtime self-test.
 */
typedef struct {
    const unsigned char *bytes;
    const unsigned char *mask;
    size_t len;
} BYTE_PATTERN;

typedef struct {
    BYTE_PATTERN entry;    /* function prologue -> match address is the entry */
    BYTE_PATTERN anchor;   /* distinctive body sequence confirming identity   */
    size_t window;         /* search for anchor within entry .. entry+window  */
    const char *desc;
} TLS_LOCATOR;

#ifdef _WIN64
/* entry: mov [rsp+10h],rbx ; mov [rsp+18h],rsi  (common to every build; the
 * bytes after this diverge by which registers the build saves, so we stop). */
static const unsigned char e_x64_b[] = {
    0x48, 0x89, 0x5C, 0x24, 0x10, 0x48, 0x89, 0x74, 0x24, 0x18 };
static const unsigned char e_x64_m[] = {
    0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF };
/* anchor: xor ebx,ebx ; cmp [LdrpActiveThreadCount],ebx ; je .. ;
 *         lea r8d,[rbx+9]   (the LoadReason==9 check -- the fingerprint). */
static const unsigned char a_x64_b[] = {
    0x33, 0xDB, 0x39, 0x1D, 0, 0, 0, 0, 0x74, 0, 0x44, 0x8D, 0x43, 0x09 };
static const unsigned char a_x64_m[] = {
    0xFF, 0xFF, 0xFF, 0xFF, 0, 0, 0, 0, 0xFF, 0, 0xFF, 0xFF, 0xFF, 0xFF };

static const TLS_LOCATOR g_locators[] = {
    { { e_x64_b, e_x64_m, sizeof(e_x64_b) },
      { a_x64_b, a_x64_m, sizeof(a_x64_b) }, 0x90,
      "x64 entry prologue + LdrpActiveThreadCount/LoadReason body anchor" },
};
#else
/* entry: push imm8 ; push <scopetable> ; call _SEH_prolog4_GS ; mov eax,ecx
 * (mov eax,ecx loads the thiscall arg from ECX -- Windows 8.1+). */
static const unsigned char e_x86_b[] = {
    0x6A, 0, 0x68, 0, 0, 0, 0, 0xE8, 0, 0, 0, 0, 0x8B, 0xC1 };
static const unsigned char e_x86_m[] = {
    0xFF, 0, 0xFF, 0, 0, 0, 0, 0xFF, 0, 0, 0, 0, 0xFF, 0xFF };
/* anchor: xor esi,esi ; test eax,eax ; jns  (the result check after
 * RtlImageDirectoryEntryToData -- Blackbone's Win11 x86 signature). */
static const unsigned char a_x86_b[] = {
    0x33, 0xF6, 0x85, 0xC0, 0x79, 0x03 };
static const unsigned char a_x86_m[] = {
    0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF };

static const TLS_LOCATOR g_locators[] = {
    { { e_x86_b, e_x86_m, sizeof(e_x86_b) },
      { a_x86_b, a_x86_m, sizeof(a_x86_b) }, 0x60,
      "x86 thiscall entry + image-directory result-check body anchor" },
};
#endif

#define NUM_LOCATORS (sizeof(g_locators) / sizeof(g_locators[0]))
#define MAX_CANDIDATES 8

static BOOL pattern_match_at(const unsigned char *p, const BYTE_PATTERN *pat)
{
    size_t i;
    for (i = 0; i < pat->len; i++) {
        if (pat->mask[i] && p[i] != pat->bytes[i])
            return FALSE;
    }
    return TRUE;
}

static int collect_candidates(unsigned char *candidates[MAX_CANDIDATES])
{
    unsigned char *base, *text;
    size_t size, off, k, li;
    int n = 0;

    if (!get_ntdll_text(&base, &text, &size))
        return 0;

    for (li = 0; li < NUM_LOCATORS; li++) {
        const TLS_LOCATOR *L = &g_locators[li];
        if (L->entry.len > size || L->anchor.len > size)
            continue;
        for (off = 0; off + L->entry.len <= size; off++) {
            size_t start, end;
            BOOL confirmed = FALSE;
            unsigned char *addr;
            int j, dup = 0;

            if (!pattern_match_at(text + off, &L->entry))
                continue;

            /* confirm the candidate via the body anchor within the window */
            start = off + L->entry.len;
            end = off + L->window;
            if (end > size - L->anchor.len)
                end = size - L->anchor.len;
            for (k = start; k <= end; k++) {
                if (pattern_match_at(text + k, &L->anchor)) {
                    confirmed = TRUE;
                    break;
                }
            }
            if (!confirmed)
                continue;

            addr = text + off;
            for (j = 0; j < n; j++)
                if (candidates[j] == addr) { dup = 1; break; }
            if (!dup) {
                candidates[n++] = addr;
                tls_log("candidate LdrpHandleTlsData @ %p (%s)",
                        (void *)addr, L->desc);
                if (n >= MAX_CANDIDATES)
                    return n;
            }
        }
    }
    return n;
}

/* ---- self-test -------------------------------------------------------- */
/*
 * Build a minimal in-memory PE that carries a single TLS slot and ask the
 * candidate function to set it up, then confirm from the live TEB that the
 * per-thread block was created and seeded from our template. Only the real
 * LdrpHandleTlsData satisfies this, so a mis-identified address is rejected.
 *
 * The synthetic image is intentionally leaked: ntdll now references it from
 * LdrpTlsList for the process lifetime (freeing it would corrupt the loader).
 */
#define ST_TLS_DIR_RVA   0x200
#define ST_TEMPLATE_RVA  0x300
#define ST_INDEX_RVA     0x400
#define ST_TEMPLATE_SIZE 8

static const unsigned char st_template[ST_TEMPLATE_SIZE] = {
    0xA1, 0xB2, 0xC3, 0xD4, 0xE5, 0xF6, 0x07, 0x18 };

#ifdef _WIN64
typedef IMAGE_TLS_DIRECTORY64 ST_TLS_DIRECTORY;
#define ST_OPT_MAGIC IMAGE_NT_OPTIONAL_HDR64_MAGIC
#define ST_MACHINE   IMAGE_FILE_MACHINE_AMD64
#else
typedef IMAGE_TLS_DIRECTORY32 ST_TLS_DIRECTORY;
#define ST_OPT_MAGIC IMAGE_NT_OPTIONAL_HDR32_MAGIC
#define ST_MACHINE   IMAGE_FILE_MACHINE_I386
#endif

static unsigned char *build_selftest_image(void)
{
    unsigned char *img;
    PIMAGE_DOS_HEADER dos;
    PIMAGE_NT_HEADERS nt;
    ST_TLS_DIRECTORY *tls;
    DWORD *index;

    img = (unsigned char *)VirtualAlloc(NULL, 0x1000,
                                        MEM_COMMIT | MEM_RESERVE,
                                        PAGE_READWRITE);
    if (!img)
        return NULL;
    memset(img, 0, 0x1000);

    dos = (PIMAGE_DOS_HEADER)img;
    dos->e_magic = IMAGE_DOS_SIGNATURE;
    dos->e_lfanew = 0x40;

    nt = (PIMAGE_NT_HEADERS)(img + 0x40);
    nt->Signature = IMAGE_NT_SIGNATURE;
    nt->FileHeader.Machine = ST_MACHINE;
    nt->FileHeader.NumberOfSections = 0;
    nt->FileHeader.SizeOfOptionalHeader = sizeof(nt->OptionalHeader);
    nt->FileHeader.Characteristics = IMAGE_FILE_DLL | IMAGE_FILE_EXECUTABLE_IMAGE;
    nt->OptionalHeader.Magic = ST_OPT_MAGIC;
    nt->OptionalHeader.ImageBase = (ULONG_PTR)img;
    nt->OptionalHeader.SectionAlignment = 0x1000;
    nt->OptionalHeader.FileAlignment = 0x200;
    nt->OptionalHeader.SizeOfImage = 0x1000;
    nt->OptionalHeader.SizeOfHeaders = 0x200;
    nt->OptionalHeader.NumberOfRvaAndSizes = IMAGE_NUMBEROF_DIRECTORY_ENTRIES;
    nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_TLS].VirtualAddress =
        ST_TLS_DIR_RVA;
    nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_TLS].Size =
        sizeof(ST_TLS_DIRECTORY);

    /* The TLS directory addresses are absolute VAs for a loaded image. */
    tls = (ST_TLS_DIRECTORY *)(img + ST_TLS_DIR_RVA);
    tls->StartAddressOfRawData = (ULONG_PTR)(img + ST_TEMPLATE_RVA);
    tls->EndAddressOfRawData = (ULONG_PTR)(img + ST_TEMPLATE_RVA + ST_TEMPLATE_SIZE);
    tls->AddressOfIndex = (ULONG_PTR)(img + ST_INDEX_RVA);
    tls->AddressOfCallBacks = 0;
    tls->SizeOfZeroFill = 0;
    tls->Characteristics = 0;

    memcpy(img + ST_TEMPLATE_RVA, st_template, ST_TEMPLATE_SIZE);

    index = (DWORD *)(img + ST_INDEX_RVA);
    *index = 0xFFFFFFFF;

    return img;
}

static PVOID *read_tls_vector(void)
{
#ifdef _WIN64
    return (PVOID *)__readgsqword(0x58);   /* TEB->ThreadLocalStoragePointer */
#else
    return (PVOID *)__readfsdword(0x2C);
#endif
}

/*
 * Returns 1 if the candidate behaves like LdrpHandleTlsData, 0 if it does not,
 * and -1 on a structural error (could not build the test image / call it).
 * The call is wrapped in SEH so a wrong candidate that faults is rejected
 * rather than crashing the process.
 */
static int run_selftest(LdrpHandleTlsData_t fn,
                        LdrLockLoaderLock_t lock, LdrUnlockLoaderLock_t unlock)
{
    unsigned char *img;
    SYNTH_LDR_ENTRY *entry;
    DWORD index = 0xFFFFFFFF;
    NTSTATUS st = (NTSTATUS)0xC0000001L;  /* STATUS_UNSUCCESSFUL */
    int ok = 0;

    img = build_selftest_image();
    if (!img)
        return -1;

    entry = (SYNTH_LDR_ENTRY *)calloc(1, sizeof(SYNTH_LDR_ENTRY));
    if (!entry) {
        /* leak img; harmless */
        return -1;
    }
    entry->DllBase = img;

    __try {
        ULONG state = 0;
        ULONG_PTR cookie = 0;
        BOOL locked = (lock && NT_SUCCESS(lock(0, &state, &cookie)));

        st = CALL_LDRP(fn, entry);

        if (locked && unlock)
            unlock(0, cookie);

        if (NT_SUCCESS(st)) {
            index = *(DWORD *)(img + ST_INDEX_RVA);
            if (index != 0xFFFFFFFF && index < 0x10000) {
                PVOID *vec = read_tls_vector();
                if (vec) {
                    unsigned char *block = (unsigned char *)vec[index];
                    if (block &&
                        memcmp(block, st_template, ST_TEMPLATE_SIZE) == 0) {
                        ok = 1;
                    }
                }
            }
        }
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
        ok = 0;
        tls_log("self-test raised exception 0x%08lx for candidate %p",
                (unsigned long)GetExceptionCode(), (void *)fn);
    }

    /*
     * Do NOT free `img` or `entry`: if the candidate was the real function it
     * registered them with ntdll for the process lifetime. If it was not, the
     * cost is one leaked page -- negligible and far safer than freeing memory
     * the loader may still reference.
     */
    tls_log("self-test for %p: status=0x%08lx index=%lu -> %s",
            (void *)fn, (unsigned long)st, (unsigned long)index,
            ok ? "OK" : "rejected");
    return ok ? 1 : 0;
}

/* ---- resolution + caching --------------------------------------------- */
static LdrpHandleTlsData_t g_fn = NULL;
static LdrLockLoaderLock_t g_lock = NULL;
static LdrUnlockLoaderLock_t g_unlock = NULL;
static int g_state = 0;   /* 0 = not yet tried, 1 = available, -1 = unavailable */

static LdrpHandleTlsData_t ensure_resolved(void)
{
    unsigned char *candidates[MAX_CANDIDATES];
    int n, i;
    HMODULE ntdll;

    if (g_state == 1)
        return g_fn;
    if (g_state == -1)
        return NULL;

    /* default to failure until a candidate passes the self-test */
    g_state = -1;

    ntdll = GetModuleHandleW(L"ntdll.dll");
    if (ntdll) {
        g_lock = (LdrLockLoaderLock_t)(void *)GetProcAddress(ntdll, "LdrLockLoaderLock");
        g_unlock = (LdrUnlockLoaderLock_t)(void *)GetProcAddress(ntdll, "LdrUnlockLoaderLock");
    }

    n = collect_candidates(candidates);
    if (n == 0) {
        tls_log("no LdrpHandleTlsData candidate found in ntdll .text "
                "(unsupported Windows build?)");
        return NULL;
    }

    for (i = 0; i < n; i++) {
        LdrpHandleTlsData_t fn = (LdrpHandleTlsData_t)(void *)candidates[i];
        if (run_selftest(fn, g_lock, g_unlock) == 1) {
            g_fn = fn;
            g_state = 1;
            tls_log("using LdrpHandleTlsData @ %p", (void *)fn);
            return g_fn;
        }
    }

    tls_log("no LdrpHandleTlsData candidate passed the self-test");
    return NULL;
}

/* ---- public entry points ---------------------------------------------- */
BOOL MemoryModuleTlsSupported(void)
{
    return ensure_resolved() != NULL;
}

BOOL MemoryModuleSetupTls(void *codeBase, PIMAGE_NT_HEADERS ntHeaders)
{
    PIMAGE_DATA_DIRECTORY dir;
    LdrpHandleTlsData_t fn;
    SYNTH_LDR_ENTRY *entry;
    NTSTATUS st;
    ULONG state = 0;
    ULONG_PTR cookie = 0;
    BOOL locked;

    if (ntHeaders->OptionalHeader.NumberOfRvaAndSizes <= IMAGE_DIRECTORY_ENTRY_TLS)
        return TRUE;  /* no TLS data directory at all */

    dir = &ntHeaders->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_TLS];
    if (dir->VirtualAddress == 0 || dir->Size == 0)
        return TRUE;  /* image has no implicit TLS -- nothing to do */

    fn = ensure_resolved();
    if (!fn) {
        tls_log("cannot set up TLS for image @ %p: "
                "LdrpHandleTlsData unavailable", codeBase);
        return FALSE;  /* hard failure: there is no fallback */
    }

    /*
     * Synthetic LDR_DATA_TABLE_ENTRY: only DllBase matters. Allocated once and
     * never freed (ntdll references it from LdrpTlsList forever).
     */
    entry = (SYNTH_LDR_ENTRY *)calloc(1, sizeof(SYNTH_LDR_ENTRY));
    if (!entry)
        return FALSE;
    entry->DllBase = codeBase;

    /* Emulate the real call site: run under the loader lock. */
    locked = (g_lock && NT_SUCCESS(g_lock(0, &state, &cookie)));
    st = CALL_LDRP(fn, entry);
    if (locked && g_unlock)
        g_unlock(0, cookie);

    if (!NT_SUCCESS(st)) {
        tls_log("LdrpHandleTlsData failed for image @ %p: status=0x%08lx",
                codeBase, (unsigned long)st);
        return FALSE;
    }

    tls_log("TLS set up for image @ %p (status=0x%08lx)",
            codeBase, (unsigned long)st);
    return TRUE;
}
