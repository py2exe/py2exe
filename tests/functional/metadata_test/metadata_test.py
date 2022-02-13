import semantic_version

v = semantic_version.Version('3.1.2')
assert v.major == 3
assert v.minor == 1
assert v.patch == 2

