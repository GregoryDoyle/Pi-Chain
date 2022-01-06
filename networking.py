'''
Helpers for networking
'''
import socket
import json

FORMAT = 'utf-8'
HEADER = 8


def close_socket(socket_toclose):
    socket_toclose.shutdown(socket.SHUT_RDWR)
    socket_toclose.close()


def create_socket():
    new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    new_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return new_socket


def package_and_send_data(client: socket, datatype: str, data):
    message = json.dumps({datatype: data}).encode(FORMAT)
    prefix = str(len(message)).encode(FORMAT)
    prefix += b' ' * (HEADER - len(prefix))
    client.send(prefix)
    client.send(message)


def receive_data(client: socket):
    data_length = int(client.recv(HEADER).decode(FORMAT))
    data = json.loads(client.recv(data_length).decode(FORMAT))
    return data
