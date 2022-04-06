#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import copy

import numpy as np

from utils.info import pktInfo


class pktRecord:
	def __init__(self, base_delay_ms=200):
		self.base_delay_ms = base_delay_ms  # 假设的传播延时
		self.packet_num = 0
		self.pkts = []  # a list of pktInfo, pktInfo 的所有网络指标，都是在一个 interval 中计算出来的
		self.last_seqNo = {}  # ssrc:last sequence number
		self.firstPktDelay = None  # ms
		self.min_seen_delay = self.base_delay_ms  # ms
		self.last_interval_recv_time = None  # ms, record the recv time of the last packet in last interval,
	
	def reset(self):
		self.packet_num = 0
		self.pkts = []
		self.last_seqNo = {}
		self.firstPktDelay = None  # ms
		self.min_seen_delay = self.base_delay_ms  # ms
		self.last_interval_recv_time = None
	
	def clear(self):
		self.packet_num = 0
		if self.pkts:
			self.last_interval_recv_time = self.pkts[-1].receive_timestamp_ms
		self.pkts = []
	
	def on_receive(self, packet_info: pktInfo):
		# 从第二个pkg开始，如果乱序，认为丢包
		assert (len(self.pkts) == 0
		        or packet_info.receive_timestamp_ms
		        >= self.pkts[-1].receive_timestamp_ms), \
			"The incoming packets receive_timestamp_ms disordered"
		
		packet_info = copy.deepcopy(packet_info)
		# Calculate the loss count
		# 与上一个 pkt 间的丢包数
		loss_count = 0
		if packet_info.ssrc in self.last_seqNo:
			loss_count = max(0,
			                 packet_info.sequence_number - self.last_seqNo[packet_info.ssrc] - 1)
		self.last_seqNo[packet_info.ssrc] = packet_info.sequence_number
		
		# Calculate packet delay
		# delay(i) = t(i) - t(0) + baseDelay
		# 认为第一个包的时延就是传播时延
		if self.firstPktDelay is None:
			self.firstPktDelay = (packet_info.receive_timestamp_ms - packet_info.send_timestamp_ms)
			delay = self.base_delay_ms
		else:
			delay = (packet_info.receive_timestamp_ms - packet_info.send_timestamp_ms) \
			        - self.firstPktDelay + self.base_delay_ms
		
		# update minimum delay
		self.min_seen_delay = min(delay, self.min_seen_delay)
		
		# Check the last interval rtime
		if self.last_interval_recv_time is None:
			self.last_interval_recv_time = packet_info.receive_timestamp_ms
		
		# Record result in current packet
		packet_info.delay = delay
		packet_info.loss_count = loss_count
		
		self.pkts.append(packet_info)
		self.packet_num += 1
	
	def _get_result_list(self, length, key):
		"""
		获取过去 length 内的 pktInfo list 字段;
		如果 length 未指定，那么就获取过去整个 interval;
		:param length:
		:param key:
		:return:
		"""
		if self.packet_num == 0:
			return []
		
		result_list = []
		if length == 0:
			length = self.pkts[-1].receive_timestamp_ms - \
			         self.last_interval_recv_time
		start_time = self.pkts[-1].receive_timestamp_ms - length
		index = self.packet_num - 1
		while index >= 0 and self.pkts[index].receive_timestamp_ms > start_time:
			result_list.append(getattr(self.pkts[index], key))
			index -= 1
		return result_list
	
	def calculate_average_delay(self, interval=0):
		"""
		Calculate the average delay in the last interval time,
		interval=0 means based on the whole packets
		The unit of return value: ms
		"""
		delay_list = self._get_result_list(length=interval, key='delay')
		if delay_list:
			return np.mean(delay_list) - self.base_delay_ms
		else:
			return 0
	
	def calculate_loss_ratio(self, interval=0):
		"""
		Calculate the loss ratio in the last interval time,
		interval=0 means based on the whole packets
		The unit of return value: packet/packet
		"""
		loss_list = self._get_result_list(length=interval, key='loss_count')
		if len(loss_list) != 0:
			loss_num = np.sum(loss_list)
			received_num = len(loss_list)
			return loss_num / (loss_num + received_num)
		else:
			return 0
	
	def calculate_receiving_rate(self, interval=0):
		"""
		Calculate the receiving rate in the last interval time,
		interval=0 means based on the whole packets
		The unit of return value: bps
		"""
		received_size_list = self._get_result_list(length=interval, key='payload_size')
		if received_size_list:
			received_nbytes = np.sum(received_size_list)
			if interval == 0:
				interval = getattr(self.pkts[-1], 'receive_timestamp_ms') - \
				           self.last_interval_recv_time
			return received_nbytes * 8 / interval * 1000  # bps
		else:
			return 0
	
	def calculate_latest_prediction(self):
		"""
		The unit of return value: bps
		"""
		if self.packet_num > 0:
			return getattr(self.pkts[-1], 'bandwidth_prediction_bps')
		else:
			return 0
