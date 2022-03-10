import argparse
import socket

FORMAT = "iso-8859-1"


class UDPEchoServer:
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
        print(f'[SERVER INITIATED] UDP ECHO Server on {self.socket}')

    def client_handler(self):
        num_packets = 0
        is_new_client = True
        while True:
            data, client_socket = self.server.recvfrom(self.packet_size)
            if is_new_client:
                print(f"[NEW CONNECTION] Client {client_socket} connected to server")
                is_new_client = False
            data = data.decode(FORMAT)
            if data:
                num_packets += 1
                print(f"[MESSAGE RECEIVED] '{data.strip()}' from {client_socket} : bytes = {len(data)}")
                response = ""
                # Client Hello
                if data.lower().strip() == "hello server":
                    response = self.get_padded_message("Hello Client")

                # Packet Size Change
                elif data.lower()[:4] == "size":
                    self.packet_size = int(data.split()[1])
                    response = self.get_padded_message(f"New Size - {self.packet_size}")
                    print(f"[PACKET SIZE] - New Packet Size - {self.packet_size}")

                elif data.lower().strip() == "disconnect":
                    response = self.get_padded_message("Disconnected")
                    print(f"[TERMINATION] - Client {client_socket} disconnected")
                    is_new_client = True

                # Reply the Same Message Back
                else:
                    response = data
                self.server.sendto(response.encode(FORMAT), client_socket)

    def get_padded_message(self, message):
        message = message.encode(FORMAT)
        if len(message) < self.packet_size:
            message += b' ' * (self.packet_size - len(message))
        return message.decode(FORMAT)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='UDP Echo Server',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-v', '--version', action='version', version='v1.0')
    parser.add_argument('-i', '--ip', type=str, metavar="IP_ADDRESS/DOMAIN_NAME",
                        help='UDP Echo Server Local IP (IPv4 or IPv6) Address or Domain Name to Port Bind to',
                        default=socket.gethostbyname(socket.gethostname()))
    parser.add_argument('-p', '--port', type=int, metavar="PORT_NUMBER",
                        help='UDP Echo Server Port Number to Port Bind to', default=7777)
    parser.add_argument('-s', '--size', type=int, metavar="PACKET_SIZE",
                        help='UDP Echo Packet Size in Bytes', default=64)

    args = parser.parse_args()

    address_info = socket.getaddrinfo(
        args.ip,
        args.port,
        proto=socket.IPPROTO_UDP
    )[0]

    server = UDPEchoServer(address_info=address_info, packet_size=args.size)
    server.client_handler()
