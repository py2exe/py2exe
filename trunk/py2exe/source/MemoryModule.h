/*
 * Memory DLL loading code
 * Version 0.0.3
 *
 * Copyright (c) 2004-2013 by Joachim Bauch / mail@joachim-bauch.de
 * http://www.joachim-bauch.de
 *
 * The contents of this file are subject to the Mozilla Public License Version
 * 2.0 (the "License"); you may not use this file except in compliance with
 * the License. You may obtain a copy of the License at
 * http://www.mozilla.org/MPL/
 *
 * Software distributed under the License is distributed on an "AS IS" basis,
 * WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
 * for the specific language governing rights and limitations under the
 * License.
 *
 * The Original Code is MemoryModule.h
 *
 * The Initial Developer of the Original Code is Joachim Bauch.
 *
 * Portions created by Joachim Bauch are Copyright (C) 2004-2013
 * Joachim Bauch. All Rights Reserved.
 *
 */

#ifndef __MEMORY_MODULE_HEADER
#define __MEMORY_MODULE_HEADER

#include <windows.h>

typedef void *HMEMORYMODULE;

typedef void *HMEMORYRSRC;

typedef void *HCUSTOMMODULE;

#ifdef __cplusplus
extern "C" {
#endif

typedef HCUSTOMMODULE (*CustomLoadLibraryFunc)(LPCSTR, void *);
typedef FARPROC (*CustomGetProcAddressFunc)(HCUSTOMMODULE, LPCSTR, void *);
typedef void (*CustomFreeLibraryFunc)(HCUSTOMMODULE, void *);

/**
 * Load DLL from memory location.
 *
 * All dependencies are resolved using default LoadLibrary/GetProcAddress
 * calls through the Windows API.
 */
HMEMORYMODULE MemoryLoadLibrary(const void *);

/**
 * Load DLL from memory location using custom dependency resolvers.
 *
 * Dependencies will be resolved using passed callback methods.
 */
HMEMORYMODULE MemoryLoadLibraryEx(const void *,
    CustomLoadLibraryFunc,
    CustomGetProcAddressFunc,
    CustomFreeLibraryFunc,
    void *);

/**
 * Get address of exported method.
 */
FARPROC MemoryGetProcAddress(HMEMORYMODULE, LPCSTR);

/**
 * Free previously loaded DLL.
 */
void MemoryFreeLibrary(HMEMORYMODULE);

/**
 * Find the location of a resource with the specified type and name.
 */
HMEMORYRSRC MemoryFindResource(HMEMORYMODULE, LPCTSTR, LPCTSTR);

/**
 * Find the location of a resource with the specified type, name and language.
 */
HMEMORYRSRC MemoryFindResourceEx(HMEMORYMODULE, LPCTSTR, LPCTSTR, WORD);

/**
 * Get the size of the resource in bytes.
 */
DWORD MemorySizeofResource(HMEMORYMODULE, HMEMORYRSRC);

/**
 * Get a pointer to the contents of the resource.
 */
LPVOID MemoryLoadResource(HMEMORYMODULE, HMEMORYRSRC);

/**
 * Load a string resource.
 */
int MemoryLoadString(HMEMORYMODULE, UINT, LPTSTR, int);

/**
 * Load a string resource with a given language.
 */
int MemoryLoadStringEx(HMEMORYMODULE, UINT, LPTSTR, int, WORD);

#ifdef __cplusplus
}
#endif

#endif  // __MEMORY_MODULE_HEADER
