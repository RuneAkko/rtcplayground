from typing import List

from utils.packetInfo import PacketInfo


class PacketGroup:
	def __init__(self, pkg_group: List[PacketInfo]):
		self.pkts = pkg_group
		self.arrival_time_list = [pkt.receive_timestamp for pkt in pkg_group]
		self.send_time_list = [pkt.send_timestamp for pkt in pkg_group]
		self.pkg_group_size = sum([pkt.size for pkt in pkg_group])
		self.pkt_num_in_group = len(pkg_group)
		
		self.complete_time = self.arrival_time_list[-1]
		self.transfer_duration = self.arrival_time_list[-1] - self.arrival_time_list[0]
