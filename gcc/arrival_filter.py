from typing import List

from utils.group import pktGroup
from utils.info import pktInfo


def condition_1(group: pktGroup, next: pktInfo):
	if len(group.pkts) == 0:
		return 0
	return next.send_timestamp_ms - group.pkts[-1].send_timestamp_ms


class ArrivalFilter:
	def __init__(self, burst):
		self.burstInterval = burst
		self.pktGroups = []
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
			if condition_1(group, ele) <= self.burstInterval:
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
		
		groupList.append(group)
		self.pktGroups = groupList
		self.groupNum = len(self.pktGroups)
	
	def measured_groupDelay_deltas(self):
		delayGradients = []
		send_delta_ts = []
		size_delta = []
		arrivalTimes = [self.pktGroups[0].arrivalTs]
		last = self.pktGroups[0]
		for group in self.pktGroups[1:]:
			send_delta = (group.sendTs - last.sendTs)
			measurement = (group.arrivalTs - last.arrivalTs) - send_delta
			last = group
			delayGradients.append(measurement)
			arrivalTimes.append(group.arrivalTs)
			send_delta_ts.append(send_delta)
			size_delta.append(group.size - last.size)
		return delayGradients, arrivalTimes, send_delta_ts, size_delta
