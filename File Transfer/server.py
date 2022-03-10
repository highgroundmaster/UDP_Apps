import argparse
import os
import socket
import time

FORMAT = "iso-8859-1"


class FileTransferServer:
    def __init__(self, address_info, packet_size):
        self.server = None
        self.socket = (address_info[4][0], address_info[4][1])
        self.packet_size = packet_size
        self.address_info = address_info
        self.initiate_server()

    def initiate_server(self):
        # Address Family - AF_INET - IPv4 , AF_INET6 - IPv6
        # SOCK_DGRAM - Socket Type - UDP
        self.server = socket.socket(self.address_info[0], socket.SOCK_DGRAM)
        # Port Bind the socket to the port
        self.server.bind(self.socket)
        print(f'[SERVER INITIATED] UDP File Transfer Server on {self.socket}')

    def client_handler(self):
        is_new_client = True
        while True:
            data, client_socket = self.server.recvfrom(self.packet_size)
            if is_new_client:
                print(f"[NEW CONNECTION] Client {client_socket} connected to server")
                is_new_client = False
            data = data.decode(FORMAT)
            if data:
                print(f"[MESSAGE RECEIVED] '{data.strip()}' from {client_socket} : bytes = {len(data)}")
                
                if data.lower()[:6] == "upload":
                    file_name, file_size = data.split()[1:]
                    file_size = int(file_size)
                    self.download(file_name, file_size, client_socket)

                elif data.lower()[:8] == "download":
                    file_name = data.split()[1]
                    self.upload(file_name, client_socket)

                # Packet Size Change
                elif data.lower()[:4] == "size":
                    self.packet_size = int(data.split()[1])
                    response = self.pad(f"New Size - {self.packet_size}")
                    print(f"[PACKET SIZE] - New Packet Size - {self.packet_size}")
                    self.server.sendto(response.encode(FORMAT), client_socket)

                elif data.lower().strip() == "disconnect":
                    response = self.pad("Disconnected")
                    print(f"[TERMINATION] - Client {client_socket} disconnected")
                    is_new_client = True
                    self.server.sendto(response.encode(FORMAT), client_socket)

    def upload(self, file_name, client_socket):
        # Send the File Name
        if file_name not in os.listdir("Server_Send"):
            print(f"[FILE UPLOAD] No {file_name} in the Server")
            message = self.pad(f"No {file_name}")
            self.server.sendto(message.encode(FORMAT), client_socket)
            return
        else:
            file_size = os.path.getsize(os.path.join("Server_Send", file_name))
            print(f"[FILE UPLOAD] Waiting to Send File - '{file_name}' to Client {client_socket}'")
            response = self.pad(f"Sending {file_name} {file_size}")

            self.server.sendto(response.encode(FORMAT), client_socket)
            response, client_socket = self.server.recvfrom(self.packet_size)
            response = response.decode(FORMAT).lower().strip()
            if response == "waiting":
                print(f"[FILE UPLOAD] Sending File - '{os.path.basename(file_name)}' to Client {client_socket}")
                # Read the contents of the file.
                with open(os.path.join("Server_Send", file_name), 'rb') as file:
                    while True:
                        contents = file.read(self.packet_size)
                        if not contents:
                            break
                        # Send Contents to Client
                        time.sleep(0.1)
                        self.server.sendto(contents, client_socket)
                file.close()

            self.server.sendto(self.pad(f"Upload Done").encode(FORMAT), client_socket)
            response, client_socket = self.server.recvfrom(self.packet_size)

            if response.decode(FORMAT).strip().lower() != "done":
                print(f"[FILE UPLOAD] '{file_name}' upload is corrupted. Resending the file to Client {client_socket}")
                self.upload(file_name, client_socket)
            else:
                print(f"[FILE UPLOAD] '{file_name}' is sent to Client {client_socket}")

    def download(self, file_name, file_size, client_socket):
        file = open(os.path.join("Server_Receive", file_name), "wb")
        response = self.pad("Waiting")
        self.server.sendto(response.encode(FORMAT), client_socket)
        print(f"[FILE DOWNLOAD] Client {client_socket} sending file '{file_name}'")
        bytes_wrote = 0
        while True:
            data, client_socket = self.server.recvfrom(self.packet_size)
            if data.decode(FORMAT).strip().lower() == 'upload done':
                if bytes_wrote < file_size:
                    print(f"[FILE DOWNLOAD] {file_name} corrupted. Requesting Client {client_socket} for Resend")
                    response = self.pad("Corrupted")
                else:
                    print(f"[FILE DOWNLOAD] File download '{file_name}' from {client_socket} complete")
                    response = self.pad("Done")

                self.server.sendto(response.encode(FORMAT), client_socket)
                break

            file.write(data)
            bytes_wrote += len(data)

        file.close()

    def pad(self, message):
        message = message.encode(FORMAT)
        if len(message) < self.packet_size:
            message += b' ' * (self.packet_size - len(message))
        return message.decode(FORMAT)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='UDP File Transfer Server',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-v', '--version', action='version', version='v1.0')
    parser.add_argument('-i', '--ip', type=str, metavar="IP_ADDRESS/DOMAIN_NAME",
                        help='UDP File Transfer Server Local IP (IPv4 or IPv6) Address or Domain Name to Port Bind to',
                        default=socket.gethostbyname(socket.gethostname()))
    parser.add_argument('-p', '--port', type=int, metavar="PORT_NUMBER",
                        help='UDP File Transfer Server Port Number to Port Bind to', default=7776)
    parser.add_argument('-s', '--size', type=int, metavar="PACKET_SIZE",
                        help='UDP Transfer Packet Size in Bytes', default=4096)

    args = parser.parse_args()

    address_info = socket.getaddrinfo(
        args.ip,
        args.port,
        proto=socket.IPPROTO_UDP
    )[0]

    server = FileTransferServer(address_info=address_info, packet_size=args.size)
    server.client_handler()
