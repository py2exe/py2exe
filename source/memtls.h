/*
 * memtls.h -- implicit Thread Local Storage support for MemoryModule.
 *
 * MemoryModule maps a PE image by hand, but never performs the implicit-TLS
 * bookkeeping the Windows loader normally does for a module that carries an
 * IMAGE_TLS_DIRECTORY (`__declspec(thread)` data): allocating a process-unique
 * TLS index, growing every thread's ThreadLocalStoragePointer array, and
 * registering the module so future threads get a per-thread copy of the TLS
 * template. Since CPython 3.12 the Python DLL and several stdlib extension
 * modules use implicit TLS, so memory-loading them (bundle_files <= 2) crashed.
 *
 * MemoryModuleSetupTls() fixes that by calling the real, unexported
 * ntdll!LdrpHandleTlsData with a synthetic LDR_DATA_TABLE_ENTRY. See
 * docs/tls-memorymodule-plan.md for the full design and rationale.
 *
 * This file is part of the py2exe run stubs; it is distributed under the same
 * MIT/X11 OR (MPL 2.0) terms as the rest of py2exe.
 */

#ifndef __MEMTLS_HEADER
#define __MEMTLS_HEADER

#include <windows.h>

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Perform implicit-TLS setup for an image that MemoryModule has just mapped at
 * `codeBase` (with NT headers `ntHeaders`). Must be called after the image is
 * mapped and relocated but before its TLS callbacks and DllMain run.
 *
 * - If the image has no TLS directory, returns TRUE immediately (no-op).
 * - Otherwise locates ntdll!LdrpHandleTlsData (once, cached and validated by a
 *   self-test) and calls it so the loader allocates the TLS index and sets up
 *   per-thread blocks for all current and future threads.
 *
 * Returns TRUE on success, FALSE on hard failure (the caller must then fail the
 * load -- there is no on-disk fallback for bundle_files <= 2).
 */
BOOL MemoryModuleSetupTls(void *codeBase, PIMAGE_NT_HEADERS ntHeaders);

/*
 * Returns TRUE if ntdll!LdrpHandleTlsData can be located and passes the
 * self-test on this machine, i.e. memory-loading implicit-TLS modules is
 * supported here. Used by the optional startup self-check; safe to call early.
 * The result is cached.
 */
BOOL MemoryModuleTlsSupported(void);

#ifdef __cplusplus
}
#endif

#endif /* __MEMTLS_HEADER */
