from typing import List

from utils.group import pktGroup
from utils.info import pktInfo


class ArrivalFilter:
	def __init__(self, burst):
		self.burstInterval = burst
		self.pktGroups = []
		self.pktsInfo = []
		self.groupNum = 0
	
	def preFilter(self, pktsInfo: List[pktInfo]):
		"""
		pre filtering，预滤波器，划分包组
		condition-1：
		发送时间在同一个 burst interval 的包，属于同一个分组
		condition-2：
		到达时间在同一个 burst interval 且 与当前组的 delay 差值 < 0
		"""
		groupList = []
		group = pktGroup()
		group.addPkt(pktsInfo[0])
		
		for ele in pktsInfo[1:]:
			if ele.receive_timestamp_ms < group.arrivalTs:
				# out of order arrivals
				continue
			if ele.send_timestamp_ms < group.sendTs:
				# out of order send/departure
				continue
			# condition-1
			if ele.send_timestamp_ms - group.pkts[-1].send_timestamp_ms <= self.burstInterval:
				group.addPkt(ele)
				continue
			# condition-2
			if ele.receive_timestamp_ms - group.arrivalTs <= self.burstInterval:
				if (ele.receive_timestamp_ms - group.arrivalTs) - (ele.send_timestamp_ms - group.sendTs) < 0:
					group.addPkt(ele)
					continue
			
			groupList.append(group)
			group = pktGroup()
			group.addPkt(ele)
		self.pktGroups = groupList
		
		self.groupNum = len(self.pktGroups)
	
	def measured_groupDelay_deltas(self):
		delayGradients = []
		arrivalTimes = [self.pktGroups[0].arrivalTs]
		last = self.pktGroups[0]
		for group in self.pktGroups[1:]:
			measurement = (last.arrivalTs - group.arrivalTs) - (last.sendTs - group.sendTs)
			last = group
			delayGradients.append(measurement)
			arrivalTimes.append(group.arrivalTs)
		return delayGradients, arrivalTimes
