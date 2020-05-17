f = open('test', 'wb')
b = b'\x00'
while b != b'\xff':
    for i in range(int.from_bytes(b, "big") + 1):
        f.write(b)
    b = int.from_bytes(b, "big") + 1
    b = b.to_bytes(1, "big")
f.close()