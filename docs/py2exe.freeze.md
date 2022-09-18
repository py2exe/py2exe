<!-- markdownlint-disable -->

# <kbd>function</kbd> `freeze`

```python
freeze(
    console=[],
    windows=[],
    data_files=None,
    zipfile='library.zip',
    options={},
    version_info={}
)
```

Create a frozen executable from the passed Python script(s). 



**Arguments:**
 
 - <b>`console`</b> (list of str):  paths of the Python files that will be frozen  as console (CLI) executables. 
 - <b>`windows`</b> (list of str):  paths of the Python files that will be frozen  as windows (GUI) executables. 
 - <b>`data_files`</b> (list):  non-Python files that have to be added in the frozen  bundle. Each element of the list is a tuple containing the destination  path in the bundle and the source path of the data files. 
 - <b>`zipfile`</b> (str):  target path of the archive that will contain all the Python  packages and modules required by the frozen bundle.  If this parameter is set to `None`, the archive will be attached  to the target executable file. 
 - <b>`options`</b> (dict):  options used to configure and customize the bundle.  Supported values are listed below. 
 - <b>`version_info`</b> (dict):  version strings and other information can be attached  to the Windows executable file by configuring this dictionary.  Supported values are listed below. 

Options (`options`): 
 - <b>`includes`</b> (list):  list of modules to include in the bundle. 
 - <b>`excludes`</b> (list):  list of modules to exclude from the bundle. 
 - <b>`packages`</b> (list):  list of packages to include in the bundle. Note: this option  is NOT recursive. Only the modules in the first level of the package will  be included. 
 - <b>`dll_excludes`</b> (list):  list of DLLs to exclude from the bundle. 
 - <b>`dest_dir`</b> (str):  target path of the bundle, default `.\dist`. 
 - <b>`compressed`</b> (int):  if `1`, create a compressed destination library archive. 
 - <b>`unbuffered`</b> (int):  if `1`, use unbuffered binary stdout and stderr. 
 - <b>`optimize`</b> (int):  optimization level of the Python files embedded in the bundle 
 - <b>`default`</b>:  `0`. Use `0` for `-O0`, `1` for `-O`, `2` for `-OO`. 
 - <b>`verbose`</b> (int):  verbosity level of the freezing process, default `0`. Supported  levels are `0--4`. 
 - <b>`bundle_files`</b> (int):  select how to bundle the Python and extension DLL files,  default `3` (all the files are copied alongside the frozen executable)/  Supported values are `3--0`. See below for further information on this  parameter. 

Bundle files levels (`bundle_files`): The py2exe runtime *can* use extension module by directly importing the from a zip-archive - without the need to unpack them to the file system. The bundle_files option specifies where the extension modules, the python DLL itself, and other needed DLLs are put. 
 - <b>`bundle_files == 3`</b>:  Extension modules, the Python DLL and other needed DLLs are  copied into the directory where the zipfile or the EXE/DLL files  are created, and loaded in the normal way. 
 - <b>`bundle_files == 2`</b>:  Extension modules are put into the library ziparchive and loaded  from it directly. The Python DLL and any other needed DLLs are copied into the  directory where the zipfile or the EXE/DLL files are created, and loaded  in the normal way. 
 - <b>`bundle_files == 1`</b>:  Extension modules and the Python DLL are put into  the zipfile or the EXE/DLL files, and everything is loaded without unpacking to  the file system.  This does not work for some DLLs, so use with  caution. 
 - <b>`bundle_files == 0`</b>:  Extension modules, the Python DLL, and other needed DLLs are put  into the zipfile or the EXE/DLL files, and everything is loaded  without unpacking to the file system.  This does not work for  some DLLs, so use with caution. 

Version information (`version_info`): Information passed in this dictionary are attached to the frozen executable and displayed in its Properties -> Details view. Supported keys: 
 - <b>`version`</b> (str):  version number 
 - <b>`description`</b> (str):  - 
 - <b>`comments`</b> (str):  - 
 - <b>`company_name`</b> (str):  - 
 - <b>`copyright`</b> (str):  - 
 - <b>`trademarks`</b> (str):  - 
 - <b>`product_name`</b> (str):  - 
 - <b>`product_version`</b> (str):  - 
 - <b>`internal_name`</b> (str):  - 
 - <b>`private_build`</b> (str):  - 
 - <b>`special_build`</b> (str):  - 

Support limitations: 
 - <b>``bundle_files <=2``</b>:  these values are supported only for packages in the Python  standard library. Issues occurring with external packages and lower values  of `bundle_files` will not be investigated. 
 - <b>``zipfile = None``</b>:  is not actively supported. Issues occurring when this  option is used will not be investigated. 


---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
