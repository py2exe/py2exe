#include <windows.h>
#include <stdio.h>

void SystemError(int error, char *msg)
{
    char Buffer[1024];
    int n;
    
    if (error) {
        LPVOID lpMsgBuf;
	FormatMessage( 
	    FORMAT_MESSAGE_ALLOCATE_BUFFER | 
	    FORMAT_MESSAGE_FROM_SYSTEM,
	    NULL,
	    error,
	    MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
	    (LPSTR)&lpMsgBuf,
	    0,
	    NULL 
	    );
        strncpy(Buffer, lpMsgBuf, sizeof(Buffer));
	LocalFree(lpMsgBuf);
    } else
	Buffer[0] = '\0';
    n = lstrlen(Buffer);
    _snprintf(Buffer+n, sizeof(Buffer)-n, msg);
    MessageBox(GetFocus(), Buffer, NULL, MB_OK | MB_ICONSTOP);
}

extern int start(int argc, char **argv);

int WINAPI
WinMain(HINSTANCE hInst, HINSTANCE hPrevInst,
	LPSTR lpCmdLine, int nCmdShow)
{
    return start(__argc, __argv);
}
