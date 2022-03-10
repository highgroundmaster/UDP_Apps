import argparse
import os
import socket
import time

FORMAT = "iso-8859-1"

class FileTransferClient:
    def __init__(self, packet_size, address_info, up_or_down, file_paths):
        # Address Family - AF_INET - IPv4 , AF_INET6 - IPv6
        # SOCK_DGRAM - Socket Type - UDP
        self.client = socket.socket(address_info[0], socket.SOCK_DGRAM)
        self.packet_size = packet_size
        self.up_or_down = up_or_down  # 1 - Upload 2 - Download
        self.file_paths = file_paths

    def server_handler(self, server_socket):
        print(f"[PINGING] Pinging Server {server_socket} : bytes = {self.packet_size}")
        if self.packet_size != 4096:
            print(f"[PACKET SIZE] Requesting Server {server_socket} for changing size to {self.packet_size}")
            message = self.pad(f"Size {self.packet_size}")
            self.client.sendto(message.encode(FORMAT), server_socket)
            # Receive message from server
            response, server_socket = self.client.recvfrom(self.packet_size)
            print(f"[PACKET SIZE] '{response.decode(FORMAT).strip()}' from {server_socket}")

        for file_path in self.file_paths:
            if self.up_or_down:
                self.upload(file_path, server_socket)
            else:
                self.download(file_path, server_socket)

        # Disconnect Message
        print(f"[TERMINATION] Requesting Server {server_socket} for disconnection")
        self.client.sendto(self.pad("Disconnect").encode(FORMAT), server_socket)
        response, server_socket = self.client.recvfrom(self.packet_size)
        print(f"[TERMINATION] '{response.decode(FORMAT).strip()}' from {server_socket} : bytes = {len(response)}")

    def upload(self, file_path, server_socket):
        # Send the File Name
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        message = self.pad(f"Upload {file_name} {file_size}")
        print(f"[FILE UPLOAD] Requesting Server {server_socket} for Sending File - '{file_name}'")
        self.client.sendto(message.encode(FORMAT), server_socket)
        response, server_socket = self.client.recvfrom(self.packet_size)
        response = response.decode(FORMAT).strip()
        if response.lower() == "waiting":
            print(f"[FILE UPLOAD] Server Accepted - '{response}' from {server_socket}")
            print(f"[FILE UPLOAD] Sending File - '{os.path.basename(file_path)}' to Server {server_socket}")
            # Read the contents of the file.
            with open(file_path, mode='rb') as file:
                while True:
                    contents = file.read(self.packet_size)
                    if not contents:
                        break
                    # Send Contents to Server
                    time.sleep(0.1)
                    self.client.sendto(contents, server_socket)
            file.close()
        self.client.sendto(self.pad(f"Upload Done").encode(FORMAT), server_socket)
        response, server_socket = self.client.recvfrom(self.packet_size)

        if response.decode(FORMAT).strip().lower() != "done":
            print(f"[FILE UPLOAD] '{file_name}' upload is corrupted. Resending the file to Server")
            self.upload(file_path, server_socket)
        else:
            print(f"[FILE UPLOAD] '{file_name}' is uploaded to Server")

    def download(self, file_name, server_socket):
        message = self.pad(f"Download {file_name}")
        print(f"[FILE DOWNLOAD] Requesting Server {server_socket} for Receiving File - '{file_name}'")
        self.client.sendto(message.encode(FORMAT), server_socket)
        response, server_socket = self.client.recvfrom(self.packet_size)
        response = response.decode(FORMAT).strip()

        if response.lower().split()[0] == "no":
            print(f"'{response}' from {server_socket}")
            return

        elif response.lower().split()[0] == "sending":
            file_size = int(response.split()[-1])
            message = self.pad("Waiting")
            self.client.sendto(message.encode(FORMAT), server_socket)
            print(f"[FILE DOWNLOAD] Server {server_socket} sending file '{file_name}'")
            file = open(os.path.join("Client_Receive", file_name), "wb")
            bytes_wrote = 0
            while True:
                data, server_socket = self.client.recvfrom(self.packet_size)
                if data.decode(FORMAT).strip().lower() == 'upload done':
                    if bytes_wrote < file_size:
                        print(f"[FILE DOWNLOAD] {file_name} corrupted. Requesting Server {server_socket} for Resend")
                        response = self.pad("Corrupted")
                    else:
                        print(f"[FILE DOWNLOAD] File download '{file_name}' from {server_socket} complete")
                        response = self.pad("Done")

                    self.client.sendto(response.encode(FORMAT), server_socket)
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
    parser = argparse.ArgumentParser(description='UDP File Transfer Client - Built over UDP Echo Client',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-v', '--version', action='version', version='v1.0')
    parser.add_argument('-i', '--ip', type=str, metavar="IP_ADDRESS/DOMAIN_NAME",
                        help='UDP File Transfer Server Local IP (IPv4 or IPv6) Address or Domain Name to Port Bind to',
                        default=socket.gethostbyname(socket.gethostname()))
    parser.add_argument('-p', '--port', type=int, metavar="PORT_NUMBER",
                        help='UDP File Transfer Server Port Number to connect to', default=7776)
    parser.add_argument('-s', '--size', type=int, help='UDP Echo Packet Size in Bytes', default=4096,
                        metavar="PACKET_SIZE")

    file_transfer_parser = parser.add_mutually_exclusive_group(required=True)
    file_transfer_parser.add_argument('-u', '--upload', nargs='+', help='Upload Specified File(s) to Server',
                                      metavar="FILE_PATH")
    file_transfer_parser.add_argument('-d', '--download', nargs='+',  metavar="FILE_PATH",
                                      help='Download Specified File(s) (if any) from Server')

    args = parser.parse_args()

    # Get IP for UDP
    address_info = socket.getaddrinfo(
        args.ip,
        args.port,
        proto=socket.IPPROTO_UDP
    )[0]

    file_paths = args.upload if args.upload else args.download

    client = FileTransferClient(
        packet_size=args.size,
        address_info=address_info,
        file_paths=file_paths,
        up_or_down=bool(args.upload)
    )

    client.server_handler(server_socket=(address_info[4][0], address_info[4][1]))
