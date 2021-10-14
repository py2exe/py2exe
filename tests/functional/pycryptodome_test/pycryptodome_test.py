import os

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

data_in = b"Test text to be encrypted."

# encrypt
key = get_random_bytes(16)
cipher = AES.new(key, AES.MODE_EAX)
ciphertext, tag = cipher.encrypt_and_digest(data_in)

file_out = open("encrypted.bin", "wb")
[ file_out.write(x) for x in (cipher.nonce, tag, ciphertext) ]
file_out.close()

# clean
tag = None
cipher = None
ciphertext = None

# decrypt
file_in = open("encrypted.bin", "rb")
nonce, tag, ciphertext = [ file_in.read(x) for x in (16, 16, -1) ]

cipher = AES.new(key, AES.MODE_EAX, nonce)
data_out = cipher.decrypt_and_verify(ciphertext, tag)
file_in.close()

# verify
print(f"'{data_in.decode('utf-8')}' should be equal to '{data_out.decode('utf-8')}'")
assert data_in == data_out

# cleanup
os.remove("encrypted.bin")
