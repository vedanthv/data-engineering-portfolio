import json
import socket
import time
import pandas as pd

def send_data_over_socket(file_path, host='spark-master', port=9999, chunk_size=2):
    s = socket.socket(socket.AF_NET,socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(1)
    print(f"Listening for connections on {host}:{port}")