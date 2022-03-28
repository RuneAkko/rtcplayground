from typing import List
from typing import Tuple

from utils.info import pktInfo
from utils.packetGroup import PacketGroup


class ArrivalFilter:
	def __init__(self):
		"""
		pacing burst time interval
		ms
		一般认为一次 burst 发出的rtp pkg 就是一帧数据，属于一个 pkg group
		"""
		self.burstInterval = 5
		self.pktGroups = []
		self.pktsInfo = []
		
		self.firstGroupCompleteTime = None
	
	def process(self, pktsInfo: List[pktInfo]):
		self.pktsInfo = pktsInfo
		self._divideGroup()
		return self._measured_deltas()
	
	def getcurrentIntervalDuration(self):
		return self.pktsInfo[0].send_timestamp_ms - self.pktsInfo[-1].send_timestamp_ms
	
	def getFirstGroupCompleteTime(self):
		return self.firstGroupCompleteTime
	
	def getLastGroupCompleteTime(self):
		return self.pktsInfo[-1].receive_timestamp_ms
	
	def getGroupNum(self):
		return len(self.pktGroups)
	
	def getCurrentIntervalIncomingBytes(self) -> int:
		_bytes = 0  # B
		for ele in self.pktGroups:
			_bytes += ele.pkg_group_size
		return _bytes
	
	def getFirstPktReceiveTime(self):
		return self.pktsInfo[0].receive_timestamp_ms
	
	def _divideGroup(self):
		"""
		将一个 interval 内的 pkgs 按 burst interval 分组
		:param pktsInfo:
		:return:
		"""
		pkgGroupList = []
		
		nailTime = self.pktsInfo[0].send_timestamp_ms
		temp = [self.pktsInfo[0]]
		for pkt in self.pktsInfo[1:]:
			if pkt.send_timestamp_ms - nailTime <= self.burstInterval:
				temp.append(pkt)
			else:
				pkgGroupList.append(PacketGroup(temp))
				# 记录 第一个 group 的接受完成时刻
				if self.firstGroupCompleteTime is None:
					self.firstGroupCompleteTime = temp[-1].receive_timestamp_ms
				nailTime = pkt.send_timestamp_ms
				temp = [pkt]
		self.pktGroups = pkgGroupList
	
	def _measured_deltas(self) -> Tuple[list, list]:
		delay_gradients = []
		complete_times = []
		for index in range(1, len(self.pktGroups)):
			send_time_delta = self.pktGroups[index].send_time_list[-1] - self.pktGroups[index - 1].send_time_list[-1]
			arrival_time_delta = self.pktGroups[index].arrival_time_list[-1] - \
			                     self.pktGroups[index - 1].arrival_time_list[-1]
			
			delay_gradient = arrival_time_delta - send_time_delta
			delay_gradients.append(delay_gradient)
			
			complete_times.append(self.pktGroups[index].complete_time)
		return delay_gradients, complete_times
