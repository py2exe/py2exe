import winrt.windows.foundation as wf

u = wf.Uri("https://github.com/")
u2 = u.combine_uri("Microsoft/xlang/tree/master/src/tool/python")
output = str(u2)

print(output)
expected = "https://github.com/Microsoft/xlang/tree/master/src/tool/python"

assert output == expected
