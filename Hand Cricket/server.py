import argparse
import socket

FORMAT = "iso-8859-1"


class UDPChatServer:
    def __init__(self, address_info, packet_size):
        self.server = None
        self.socket = (address_info[4][0], address_info[4][1])
        self.packet_size = packet_size
        self.address_info = address_info
        self.active_clients = {}
        self.initiate_server()

    def initiate_server(self):
        # Address Family - AF_INET - IPv4 , AF_INET6 - IPv6
        # SOCK_DGRAM - Socket Type - UDP
        self.server = socket.socket(self.address_info[0], socket.SOCK_DGRAM)
        # Port Bind the socket to the port
        self.server.bind(self.socket)
        print(f'[SERVER INITIATED] UDP File Transfer Server on {self.socket}')

    def client_handler(self):
        """
        Handles all the interactions with Client(s)
        """

        while True:
            data, client_socket = self.server.recvfrom(self.packet_size)
            data = data.decode(FORMAT)
            if data:
                print(f"[MESSAGE RECEIVED] '{data.strip()}' from {client_socket} : bytes = {len(data)}")
                if data.lower()[:4] == "user":
                    self.new_client(user_name=data.split()[1], client_socket=client_socket)

                # Message
                elif data.lower()[:4] == "chat":
                    dest_username = data.split()[1]
                    message = ' '.join(data.split()[2:]) if len(data.split()) > 2 else ''
                    self.send_message(self.find_user_by_socket(client_socket), dest_username, message)

                # Packet Size Change
                elif data.lower()[:4] == "size":
                    self.packet_size = int(data.split()[1])
                    response = self.pad(f"New Size - {self.packet_size}")
                    print(f"[PACKET SIZE] - New Packet Size - {self.packet_size}")
                    self.server.sendto(response.encode(FORMAT), client_socket)

                elif data.lower().strip() == "disconnect":
                    self.disconnect(self.find_user_by_socket(client_socket))

    def new_client(self, user_name, client_socket):
        """
        Registers the Client into Server
        :param user_name: Username of the Client
        :param client_socket: (IP, Port) of the Client
        """
        response = ""
        if self.active_clients.get(user_name):
            print(f"[SIGN IN] Username already taken")
            response = self.pad(f"Taken - {user_name}")
        else:
            self.active_clients[user_name] = client_socket
            print(f"[SIGN IN] Client {user_name} - {client_socket} signed in to Server")
        self.server.sendto(response.encode(FORMAT), client_socket)

    def disconnect(self, user_name):
        """
        Disconnects a Client from Server
        :param user_name: Username of the Client
        """
        print(f"[SIGN OUT] {user_name} - {self.active_clients[user_name]} disconnected")
        response = self.pad("Disconnected")
        self.server.sendto(response.encode(FORMAT), self.active_clients[user_name])
        self.active_clients.pop(user_name)

    def find_user_by_socket(self, client_socket):
        for username, active_socket in self.active_clients.items():
            if client_socket == active_socket:
                return username
        return None

    def send_message(self, source_username, dest_username, message):
        """
        Sends Messages from Source Client to Destination Client
        :param source_username: Username of the Source Client
        :param dest_username: Username of the Destination Client
        :param message: Message to be sent
        """
        # If provided destination not in registered clients
        if dest_username not in self.active_clients.keys():
            print(f"[USER ERROR] {dest_username} not found or inactive")
            response = self.pad(f"No {dest_username} found")
            self.server.sendto(response.encode(FORMAT), self.active_clients[source_username])

        # Send message to destination
        else:
            print(f"[CHAT] Sending message from {self.active_clients[source_username]} to "
                  f"{self.active_clients[dest_username]}")
            if message != '':
                response = self.pad(f"Chat {source_username} {message}")
            else:
                response = self.pad(f"Chat {source_username}")
            self.server.sendto(response.encode(FORMAT), self.active_clients[dest_username])

    def pad(self, message):
        """
        Pads the given message upto Packet Size Amount
        :param message:
        :return: string - Padded String
        """
        message = message.encode(FORMAT)
        if len(message) < self.packet_size:
            message += b' ' * (self.packet_size - len(message))
        return message.decode(FORMAT)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='UDP Chat Server',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-v', '--version', action='version', version='v1.0')
    parser.add_argument('-i', '--ip', type=str, metavar="IP_ADDRESS/DOMAIN_NAME",
                        help='UDP Chat Server Local IP (IPv4 or IPv6) Address or Domain Name to Port Bind to',
                        default=socket.gethostbyname(socket.gethostname()))
    parser.add_argument('-p', '--port', type=int, metavar="PORT_NUMBER",
                        help='UDP Chat Server Port Number to Port Bind to', default=7776)
    parser.add_argument('-s', '--size', type=int, metavar="PACKET_SIZE",
                        help='UDP Chat Packet Size in Bytes', default=1024)

    args = parser.parse_args()

    address_info = socket.getaddrinfo(
        args.ip,
        args.port,
        proto=socket.IPPROTO_UDP
    )[0]

    # instantiates server
    server = UDPChatServer(address_info=address_info, packet_size=args.size)
    server.client_handler()
