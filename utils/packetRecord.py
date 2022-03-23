#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np


class PacketRecord:
	# feature_interval can be modified
	# ? what's the meaning of base delay arg?
	def __init__(self, base_delay_ms=200):
		self.base_delay_ms = base_delay_ms
		"""
		ms
		decision-making interval
		
		"""
		self.packet_num = 0
		self.pkt_stats_list = []
		"""
		is a list of pks , which  is a dict below:
		{
			'timestamp': packet_info.receive_timestamp,  # ms
			'delay': delay,  # ms
			'payload_byte': packet_info.payload_size,  # B
			'loss_count': loss_count,  # p
			'bandwidth_prediction': packet_info.bandwidth_prediction  # bps
		}
		"""
		self.last_seqNo = {}
		"""
		dict : ssrc-last sequence number
		某 ssrc 的最新 seqNo
		"""
		self.firstPktTotDelay = None
		"""
		ms,
		
		
		"""
		self.min_seen_delay = self.base_delay_ms  # ms
		"""
		min of delay
		
		"""
		self.last_interval_rtime = None
		"""
		ms, record the rtime of the last packet in last interval,
		在上一个决策间隔中，记录到最后一个包的到达时间
		"""
	
	def reset(self):
		self.packet_num = 0
		self.pkt_stats_list = []  # ms
		self.last_seqNo = {}
		self.firstPktTotDelay = None  # ms
		self.min_seen_delay = self.base_delay_ms  # ms
		self.last_interval_rtime = None
	
	def clear(self):
		self.packet_num = 0
		if self.pkt_stats_list:
			self.last_interval_rtime = self.pkt_stats_list[-1]['timestamp']
		self.pkt_stats_list = []
	
	def on_receive(self, packet_info):
		# 从第二个pkg开始，如果乱序，认为丢包
		assert (len(self.pkt_stats_list) == 0
		        or packet_info.receive_timestamp
		        >= self.pkt_stats_list[-1]['timestamp']), \
			"The incoming packets receive_timestamp disordered"
		
		# Calculate the loss count
		loss_count = 0
		if packet_info.ssrc in self.last_seqNo:
			loss_count = max(0,
			                 packet_info.sequence_number - self.last_seqNo[packet_info.ssrc] - 1)
		self.last_seqNo[packet_info.ssrc] = packet_info.sequence_number
		
		# Calculate packet delay
		# delay(i) = t(i) - t(0) + baseDelay
		# delay 是除传播时延的总和
		if self.firstPktTotDelay is None:
			self.firstPktTotDelay = (packet_info.receive_timestamp - packet_info.send_timestamp)
			delay = self.base_delay_ms
		else:
			delay = (packet_info.receive_timestamp - packet_info.send_timestamp) \
			        - self.firstPktTotDelay + self.base_delay_ms
		
		# update minimum delay
		self.min_seen_delay = min(delay, self.min_seen_delay)
		
		# Check the last interval rtime
		if self.last_interval_rtime is None:
			self.last_interval_rtime = packet_info.receive_timestamp
		
		# Record result in current packet
		packet_result = {
			'timestamp': packet_info.receive_timestamp,  # ms
			'delay': delay,  # ms
			'payload_byte': packet_info.payload_size,  # B
			'loss_count': loss_count,  # p
			'bandwidth_prediction': packet_info.bandwidth_prediction  # bps
		}
		self.pkt_stats_list.append(packet_result)
		self.packet_num += 1
	
	def _get_result_list(self, interval, key):
		"""
		获取过去 interval 内的 pkt list key 字段
		:param interval:
		:param key:
		:return:
		"""
		if self.packet_num == 0:
			return []
		
		result_list = []
		if interval == 0:
			interval = self.pkt_stats_list[-1]['timestamp'] - \
			           self.last_interval_rtime
		start_time = self.pkt_stats_list[-1]['timestamp'] - interval
		index = self.packet_num - 1
		while index >= 0 and self.pkt_stats_list[index]['timestamp'] > start_time:
			result_list.append(self.pkt_stats_list[index][key])
			index -= 1
		return result_list
	
	def calculate_average_delay(self, interval=0):
		"""
		Calculate the average delay in the last interval time,
		interval=0 means based on the whole packets
		The unit of return value: ms
		"""
		delay_list = self._get_result_list(interval=interval, key='delay')
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
		loss_list = self._get_result_list(interval=interval, key='loss_count')
		if loss_list:
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
		received_size_list = self._get_result_list(interval=interval, key='payload_byte')
		if received_size_list:
			received_nbytes = np.sum(received_size_list)
			if interval == 0:
				interval = self.pkt_stats_list[-1]['timestamp'] - \
				           self.last_interval_rtime
			return received_nbytes * 8 / interval * 1000
		else:
			return 0
	
	def calculate_latest_prediction(self):
		"""
		The unit of return value: bps
		"""
		if self.packet_num > 0:
			return self.pkt_stats_list[-1]['bandwidth_prediction']
		else:
			return 0
