from typing import List
from typing import Tuple

from utils.packetGroup import PacketGroup
from utils.packetInfo import PacketInfo


class ArrivalFilter:
	def __init__(self):
		"""
		pacing burst time interval
		ms
		一般认为一次 burst 发出的rtp pkg 就是一帧数据，属于一个 pkg group
		"""
		self.burstInterval = 5
		self.pktGroups = []
	
	def _divideGroup(self, pktsStates: List[PacketInfo]):
		"""
		将一个 interval 内的 pkgs 按 burst interval 分组
		:param pktsStates:
		:return:
		"""
		pkgGroupList = []
		
		nailTime = pktsStates[0].send_timestamp
		temp = [pktsStates[0]]
		for pkt in pktsStates[1:]:
			if pkt.send_timestamp - nailTime <= self.burstInterval:
				temp.append(pkt)
			else:
				pkgGroupList.append(PacketGroup(temp))
				# 记录 第一个 group 的接受完成时刻
				nailTime = pkt.send_timestamp
				temp = [pkt]
		self.pktGroups = pkgGroupList
	
	# return pkgGroupList
	
	def _measured_deltas(self) -> Tuple[list, list]:
		delay_gradients = []
		for index in range(1, len(self.pktGroups)):
			send_time_delta = self.pktGroups[index].send_time_list[-1] - self.pktGroups[index - 1].send_time_list[-1]
			arrival_time_delta = self.pktGroups[index].arrival_time_list[-1] - \
			                     self.pktGroups[index - 1].arrival_time_list[-1]
			
			delay_gradient = arrival_time_delta - send_time_delta
			delay_gradients.append(delay_gradient)
		return delay_gradients, []
