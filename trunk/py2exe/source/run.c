#include <windows.h>
#include <stdio.h>

void SystemError(int error, char *msg)
{
    char Buffer[1024];
    
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
	fprintf(stderr, Buffer);
    } else
	fprintf(stderr, msg);
}

extern int start(int argc, char **argv);

int main (int argc, char **argv)
{
    return start(argc, argv);
}
