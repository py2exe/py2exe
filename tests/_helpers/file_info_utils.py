import pefile


def get_file_version_info(file_name):
    """Borrowed from https://stackoverflow.com/questions/580924/how-to-access-a-files-properties-on-windows"""
    pe = pefile.PE(file_name, fast_load=True)
    pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_RESOURCE']])
    res = {}
    for idx in range(len(pe.VS_VERSIONINFO)):
        if hasattr(pe, 'FileInfo') and len(pe.FileInfo) > idx:
            for entry in pe.FileInfo[idx]:
                if hasattr(entry, 'StringTable'):
                    for st_entry in entry.StringTable:
                        for str_entry in sorted(list(st_entry.entries.items())):
                            res[str_entry[0].decode('utf-8', 'backslashreplace')]  = str_entry[1].decode('utf-8', 'backslashreplace')
    return res
