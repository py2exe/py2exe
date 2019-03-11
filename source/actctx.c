#include "actctx.h"

HANDLE PyWin_DLLhActivationContext=NULL;
PFN_GETCURRENTACTCTX pfnGetCurrentActCtx=NULL;
PFN_ACTIVATEACTCTX pfnActivateActCtx=NULL;
PFN_DEACTIVATEACTCTX pfnDeactivateActCtx=NULL;
PFN_ADDREFACTCTX pfnAddRefActCtx=NULL;
PFN_RELEASEACTCTX pfnReleaseActCtx=NULL;

void _MyLoadActCtxPointers()
{
	HINSTANCE hKernel32 = GetModuleHandleW(L"kernel32.dll");
	if (hKernel32)
		pfnGetCurrentActCtx = (PFN_GETCURRENTACTCTX) GetProcAddress(hKernel32, "GetCurrentActCtx");
	// If we can't load GetCurrentActCtx (ie, pre XP) , don't bother with the rest.
	if (pfnGetCurrentActCtx) {
		pfnActivateActCtx = (PFN_ACTIVATEACTCTX) GetProcAddress(hKernel32, "ActivateActCtx");
		pfnDeactivateActCtx = (PFN_DEACTIVATEACTCTX) GetProcAddress(hKernel32, "DeactivateActCtx");
		pfnAddRefActCtx = (PFN_ADDREFACTCTX) GetProcAddress(hKernel32, "AddRefActCtx");
		pfnReleaseActCtx = (PFN_RELEASEACTCTX) GetProcAddress(hKernel32, "ReleaseActCtx");
	}
}

ULONG_PTR _My_ActivateActCtx()
{
	ULONG_PTR ret = 0;
	if (PyWin_DLLhActivationContext && pfnActivateActCtx)
		if (!(*pfnActivateActCtx)(PyWin_DLLhActivationContext, &ret)) {
			OutputDebugStringA("py2exe failed to activate the activation context before loading a DLL\n");
			ret = 0; // no promise the failing function didn't change it!
		}
	return ret;
}

void _My_DeactivateActCtx(ULONG_PTR cookie)
{
	if (cookie && pfnDeactivateActCtx)
		if (!(*pfnDeactivateActCtx)(0, cookie))
			OutputDebugStringA("py2exe failed to de-activate the activation context\n");
}
