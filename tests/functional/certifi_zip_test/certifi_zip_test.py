import certifi
import os

print(certifi.where())
assert os.path.exists(certifi.where())