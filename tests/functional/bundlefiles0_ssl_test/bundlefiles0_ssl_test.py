import socket
import ssl

# SET VARIABLES
packet = b"GET / HTTP/1.1\r\nHost: www.google.com\r\n\r\n"
HOST, PORT = 'www.google.com', 443

# CREATE SOCKET
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(10)

# WRAP SOCKET (ssl.wrap_socket was removed in Python 3.12)
context = ssl.create_default_context()
wrappedSocket = context.wrap_socket(sock, server_hostname=HOST)

# CONNECT AND PRINT REPLY
wrappedSocket.connect((HOST, PORT))
wrappedSocket.send(packet)
rec = wrappedSocket.recv(15)

# CLOSE SOCKET CONNECTION
wrappedSocket.close()

# PRINT OUTPUT

out = rec.decode('utf-8')
print("SSL test output: {}".format(out))
assert out == 'HTTP/1.1 200 OK'
