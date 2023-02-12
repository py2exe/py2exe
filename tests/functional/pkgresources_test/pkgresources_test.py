import pkg_resources

v_small = pkg_resources.parse_version("1.0")
v_large = pkg_resources.parse_version("2.0")

print(f'pkg_resources: testing if version {v_small} < {v_large}...')
assert v_small < v_large
