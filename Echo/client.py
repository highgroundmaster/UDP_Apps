import argparse
import asyncio
import socket
from datetime import datetime
import matplotlib.pyplot as plt

FORMAT = "iso-8859-1"


class UDPEchoClient:
    def __init__(self, packet_size, address_info, interval, num_packets, message, do_graph):
        # Address Family - AF_INET - IPv4 , AF_INET6 - IPv6
        # SOCK_DGRAM - Socket Type - UDP
        self.client = socket.socket(address_info[0], socket.SOCK_DGRAM)
        self.packet_size = packet_size
        self.interval = interval
        self.num_packets = num_packets
        self.message = self.get_padded_message(message)
        self.do_graph = do_graph
        self.average_throughput = []
        self.average_delay = []
        self._throughput_sec = []
        self._delay_sec = []

    async def server_handler(self, server_socket):
        rtt_values = []
        throughput = []
        num_received = 0
        print(f"[PINGING] Pinging Server {server_socket} : bytes = {self.packet_size}")
        if self.packet_size != 64:
            print(f"[PACKET SIZE] Requesting Server {server_socket} for changing size to {self.packet_size}")
            message = self.get_padded_message(f"Size {self.packet_size}")
            self.client.sendto(message.encode(FORMAT), server_socket)
            # Receive message from server
            response, server_socket = self.client.recvfrom(self.packet_size)
            print(f"[PACKET SIZE] '{response.decode(FORMAT).strip()}' from {server_socket}")
        await asyncio.sleep(0)

        for packet in range(self.num_packets):
            # Timestamp before sending message
            before_request = datetime.now()
            self.client.sendto(self.message.encode(FORMAT), server_socket)
            # Receive message from server
            response, server_socket = self.client.recvfrom(self.packet_size)
            # Timestamp after receiving message
            after_response = datetime.now()
            rtt_time = (after_response - before_request).total_seconds() * 1000
            rtt_values.append(rtt_time)
            throughput.append(self.packet_size * 8 / rtt_time)

            # Find delay
            self._delay_sec.append(rtt_time)
            self._throughput_sec.append(self.packet_size * 8 / rtt_time)

            print(f"[MESSAGE RECEIVED] '{response.decode(FORMAT).strip()}' from {server_socket} : "
                  f"bytes = {len(response)} time = {round(rtt_time, 4)} ms")
            num_received += 1
            await asyncio.sleep(self.interval)

        self.do_graph = False
        # Disconnect Message
        print(f"[TERMINATION] Requesting Server {server_socket} for disconnection")
        self.client.sendto(self.get_padded_message("Disconnect").encode(FORMAT), server_socket)
        response, server_socket = self.client.recvfrom(self.packet_size)
        print(f"[TERMINATION] '{response.decode(FORMAT).strip()}' from {server_socket} : bytes = {len(response)}")

        # Print Echo Statistics
        print()
        self.print_statistics(num_received, rtt_values, server_socket)

    def get_padded_message(self, message):
        message = message.encode(FORMAT)
        if len(message) < self.packet_size:
            message += b' ' * (self.packet_size - len(message))
        return message.decode(FORMAT)

    def print_statistics(self, num_received, rtt_values, server_socket):
        """
        Print Ping like statistics
        :param num_received: Number of packets received
        :param rtt_values: RTT Values of all packets received
        :param server_socket: (IP, Port) of Server
        """

        print(f"Echo Statistics for {server_socket}:")
        print(f"\t Packets : Sent = {self.num_packets + 1}, Received = {num_received + 1}, "
              f"Lost {self.num_packets - num_received} ({self.get_loss_percentage(num_received)}% Loss) ")
        print("Approximate Round-Trip Times in milli-seconds (ms):")
        rtt_stats = self.rtt_statistics(rtt_values)
        print(f"\t Minimum = {rtt_stats[2]}ms, Maximum = {rtt_stats[1]}ms, Average = {rtt_stats[0]}ms")

    def get_loss_percentage(self, num_received):
        return round(((self.num_packets - num_received) / self.num_packets * 100), 4)

    @staticmethod
    def rtt_statistics(rtt_values):
        """
        Calculate RTT Statistics
        :param rtt_values: RTT Values of all packets received
        :return: Average, Minimum and Maximum of RTTs
        """

        rtt_avg = round(sum(rtt_values) / len(rtt_values), 4)
        rtt_max = round(max(rtt_values), 4)
        rtt_min = round(min(rtt_values), 4)
        return rtt_avg, rtt_max, rtt_min

    async def throughput_delay_statistics(self):
        """
        Runs every second to calculate average throughput and delay and appends them in a list
        """
        while self.do_graph:
            try:
                self.average_delay.append(round(sum(self._delay_sec) / len(self._delay_sec), 4))
                self.average_throughput.append(round(sum(self._throughput_sec) / len(self._throughput_sec), 4))
                self._delay_sec = []
                self._throughput_sec = []
                self.interval *= 0.9
            except ZeroDivisionError:
                self.average_throughput.append(0)
                self.average_delay.append(self.interval * 1000)
            await asyncio.sleep(1)

    def plot_iperf_graph(self, do_graph):
        """
        Plots the graph of the calculated throughput and delay
        :param do_graph:  Boolean for plotting graph or otherwise
        """
        if do_graph:
            # Create a Figure
            iperf_fig, (ax_throughput, ax_delay) = plt.subplots(2, 1, figsize=(10, 20))
            iperf_fig.suptitle('IPERF Plots', fontsize=20)
            iperf_fig.tight_layout(pad=8, h_pad=10)

            # Throughput Plot
            ax_throughput.set_title("Average Throughput per sec", fontsize=16)
            ax_throughput.set_ylabel("Throughput (bps)", fontsize=12)
            ax_throughput.plot(range(len(self.average_throughput)), self.average_throughput)
            ax_throughput.axis([0, len(self.average_throughput) - 1, 0, max(self.average_throughput) + 100])
            ax_throughput.grid(True)
            # Delay Plot
            ax_delay.set_title("Average Delay per sec", fontsize=16)
            ax_delay.set_ylabel("Average Delay (ms)", fontsize=12)
            ax_delay.set_xlabel("Time (s)", fontsize=12)
            ax_delay.set_yscale('log')
            ax_delay.set_xlim([0, len(self.average_delay) - 1])
            ax_delay.plot(range(len(self.average_delay)), self.average_delay)
            ax_delay.grid(True)

            # Display all open figures
            plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='UDP Echo Client',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-v', '--version', action='version', version='v1.0')
    parser.add_argument('-i', '--ip', type=str, metavar="IP_ADDRESS/DOMAIN_NAME",
                        help='UDP Echo Server Local IP (IPv4 or IPv6) Address or Domain Name to Port Bind to',
                        default=socket.gethostbyname(socket.gethostname()))
    parser.add_argument('-p', '--port', type=int, metavar="PORT_NUMBER",
                        help='UDP Echo Server Port Number to connect to', default=7777)
    parser.add_argument('-m', '--message', type=str,
                        help='UDP Echo Message to send', default="Hello Server")
    parser.add_argument('-n', '--num_packets', type=int,
                        help='Number of UDP Echo Packets to send', default=5)
    parser.add_argument('-s', '--size', type=int, metavar="PACKET_SIZE",
                        help='UDP Echo Packet Size in Bytes', default=64)
    parser.add_argument('-t', '--interval', type=float, metavar="TIME",
                        help='UDP Echo Message Interval in sec', default=1)
    parser.add_argument('-g', '--graph', default=False, action='store_true', help="Enable iperf Graph for throughput "
                                                                                  "and delay")
    parser.set_defaults(graph=False)

    args = parser.parse_args()
    # Get IP for UDP
    address_info = socket.getaddrinfo(
        args.ip,
        args.port,
        proto=socket.IPPROTO_UDP
    )[0]

    client = UDPEchoClient(
        packet_size=args.size,
        address_info=address_info,
        interval=args.interval,
        message=args.message,
        num_packets=args.num_packets,
        do_graph=args.graph
    )

    loop = asyncio.get_event_loop()

    loop.run_until_complete(
        asyncio.gather(
            client.server_handler(
                server_socket=(
                    address_info[4][0],
                    address_info[4][1])),
            client.throughput_delay_statistics()
        )
    )

    client.plot_iperf_graph(args.graph)
