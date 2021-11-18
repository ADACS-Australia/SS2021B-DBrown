import socket


def test_port_open(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # connect_ex returns 0 if the connection was successful
    result = sock.connect_ex(("127.0.0.1", int(port))) == 0
    sock.close()
    return result
