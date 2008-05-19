"C:\Python23\Removepy2exe.exe" -u "C:\Python23\py2exe-wininst.log"
"C:\Python24\Removepy2exe.exe" -u "C:\Python24\py2exe-wininst.log"
"C:\Python25\Removepy2exe.exe" -u "C:\Python25\py2exe-wininst.log"

for %%f in (..\dist\py2exe*.exe) do (
    "%%f"
)

for %%f in (..\dist\py2exe*.msi) do (
    "%%f"
)
