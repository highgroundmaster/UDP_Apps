import argparse
import socket
import threading
import time
from tkinter import *

FORMAT = "iso-8859-1"

# Dark Background Themes
BG_COLOUR = ["#282828", "#383838", "#001122", "#102a44"]
FG_COLOUR = ["#FFFFFF", "#8BADC1"]
FONT_STYLE = "Lucida Console"


class UDPChatClient:
    def __init__(self, packet_size, address_info, username, server_socket):
        """
        UDP based Chat Client
        :param packet_size: Amount of Information sent per message in Bytes
        :param address_info: Address Info got from the `socket.getAddrInfo` for Server
        :param username: Username of the Client
        :param server_socket: (IP, Port) of the server
        """
        # Address Family - AF_INET - IPv4 , AF_INET6 - IPv6
        # SOCK_DGRAM - Socket Type - UDP
        self.client = socket.socket(address_info[0], socket.SOCK_DGRAM)
        self.server_socket = server_socket
        self.packet_size = packet_size
        self.username = username
        self.dest_username = ''

        # Main Chat Window
        self.window = Tk()
        # At the Moment Hide, Open when recipient configured
        self.window.withdraw()

    def server_handler(self):
        """"
        Starts the Interaction with the Server for Chat
        """
        # Sign in
        self.sign_in()
        print()

        # Change Packet Size
        if self.packet_size != 1024:
            print(f"[PACKET SIZE] Requesting Server {self.server_socket} for changing size to {self.packet_size}")
            message = self.pad(f"Size {self.packet_size}")
            self.client.sendto(message.encode(FORMAT), self.server_socket)
            # Receive message from server
            response, self.server_socket = self.client.recvfrom(self.packet_size)
            print(f"[PACKET SIZE] '{response.decode(FORMAT).strip()}' from {self.server_socket}")

        # Chat
        self._get_recipient()
        receiver = threading.Thread(target=self.receive)
        receiver.start()
        self.gui_run()
        self.disconnect()

    def sign_in(self):
        """
        Signs in with the server with the username

        If username already taken, repeats the process
        """
        while True:
            message = self.pad(f"User {self.username}")
            self.client.sendto(message.encode(FORMAT), self.server_socket)
            response, self.server_socket = self.client.recvfrom(self.packet_size)
            response = response.decode(FORMAT).strip()
            if response.lower()[:5] == "taken":
                print(f"[USERNAME ERROR] Username '{self.username}' already taken, please provide another one")
                self.username = input("Enter New Username : ")
            else:
                print(f"[SIGN IN] Successfully Signed in to Server {self.server_socket}")
                break

    def _get_recipient(self):
        """
        Interacts with Server to connect with the Recipient

        Repeats until given an active username
        """
        while True:
            dest_username = input("Enter the Username of the Recipient : ")
            message = self.pad(f"Chat {dest_username}")
            self.client.sendto(message.encode(FORMAT), self.server_socket)
            response, self.server_socket = self.client.recvfrom(self.packet_size)
            response = response.decode(FORMAT).strip()
            if response.lower()[:2] == "no":
                print(f"[USERNAME ERROR] Username '{dest_username}' not found, please provide another one")
            else:
                print(f"[CHAT ROOM] Successfully entered the chatroom with {dest_username}")
                self.dest_username = dest_username
                break

    def disconnect(self):
        # Disconnect Message
        print(f"[SIGN OUT] Disconnecting from Server {self.server_socket}")
        self.client.sendto(self.pad("Disconnect").encode(FORMAT), self.server_socket)
        exit(0)

    def send(self):
        """
        Takes the message from Tkinter Message Box on Send Button

        Sends the message to Server

        Inserts the message onto the Tkinter Chat Box
        """
        message = self.message_box.get()
        if message.lower() == "disconnect":
            self.disconnect()

        # Insert the Message on Chat Box
        self.chat_box.insert(END, f"You : {message}")
        # Send Message To Server
        message = self.pad(f"Chat {self.dest_username} " + message)
        self.client.sendto(message.encode(FORMAT), self.server_socket)

    def sender_thread(self):
        sender = threading.Thread(target=self.send)
        sender.start()

    def receive(self):
        """
        Receives messages from Server, processes and inserts on Tkinter Chat Box
        """
        while True:
            response, self.server_socket = self.client.recvfrom(self.packet_size)
            response = response.decode(FORMAT).strip()
            if response.lower() == f"no {self.dest_username} found":
                message = f"{self.dest_username} disconnected from Server"
                self.disconnect()
                break
            elif response.lower() == "disconnected":
                break
            else:
                response = response.split()
                message = f"{response[1]} : {' '.join(response[2:])}"
            # Insert the message on Chat Box
            time.sleep(0.1)
            self.chat_box.insert(END, message)

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

    def gui_run(self):
        """
        Runs the Tkinter Chat Window
        """
        self._window_layout()
        self.window.mainloop()

    def _window_layout(self):
        """
        Chat Window Layout
        """
        # Open Window Now
        self.window.deiconify()
        # Main Skeleton of the Chat Window
        self.window.title(self.username)
        self.window.resizable(width=False, height=False)
        self.window.configure(width=300, height=500, bg=BG_COLOUR[0])
        # self.window.iconbitmap("Chat_Icon.ico")

        # Message Entry Box
        message = StringVar()
        self.message_box = Entry(self.window, textvariable=message, border=2, width=32)
        self.message_box.configure(background=BG_COLOUR[1], foreground=FG_COLOUR,
                                   font=(FONT_STYLE, 10, "bold"))
        self.message_box.place(x=10, y=440)

        # create a Send Button - Self.image So no Garbage Collection
        self.button_image = PhotoImage(file="Send_Button.png")
        # button_image = button_image.subsample(2)
        send_button = Button(self.window, image=self.button_image,
                             command=self.sender_thread, borderwidth=0)
        send_button.configure(background=BG_COLOUR[0], highlightbackground=BG_COLOUR[1], highlightthickness=0)
        # Place the Send Button in the Chat Window
        send_button.place(x=250, y=430)

        # Chat Box
        self.chat_box = Listbox(self.window, height=30, width=38)
        self.chat_box.configure(background=BG_COLOUR[1],  foreground=FG_COLOUR)
        # Place the Chat Box Inside thw Window
        self.chat_box.place(x=15, y=20)
        # Place the scroll bar on Chat Box
        scroll_bar = Scrollbar(self.chat_box)
        scroll_bar.place(relheight=1, relx=0.974)

        scroll_bar.config(command=self.chat_box.yview)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='UDP Hand Cricket Client - Built over UDP Echo Client',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-v', '--version', action='version', version='v1.0')
    parser.add_argument('-i', '--ip', type=str, metavar="IP_ADDRESS/DOMAIN_NAME",
                        help='UDP Hand Cricket Server Local IP (IPv4 or IPv6) Address or Domain Name to Port Bind to',
                        default=socket.gethostbyname(socket.gethostname()))
    parser.add_argument('-p', '--port', type=int, metavar="PORT_NUMBER",
                        help='UDP Hand Cricket Server Port Number to connect to', default=7776)
    parser.add_argument('-s', '--size', type=int, help='UDP Hand Cricket Packet Size in Bytes', default=20,
                        metavar="PACKET_SIZE")
    parser.add_argument('-u', '--username', help='Username Client Wants to use',
                        metavar="USER_NAME", required=True)

    args = parser.parse_args()

    # Get IP for UDP
    address_info = socket.getaddrinfo(
        args.ip,
        args.port,
        proto=socket.IPPROTO_UDP
    )[0]

    # Instantiate Client
    client = UDPChatClient(
        username=args.username,
        packet_size=args.size,
        address_info=address_info,
        server_socket=(address_info[4][0], address_info[4][1])
    )

    client.server_handler()
