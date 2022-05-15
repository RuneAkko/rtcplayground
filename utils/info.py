#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class pktInfo:
	def __init__(self):
		self.payload_type = None
		self.sequence_number = None  # int
		self.send_timestamp_ms = None  # int, ms
		self.ssrc = None  # int ssrc_id
		self.receive_timestamp_ms = None  # int, ms
		self.padding_length = None  # int, B
		self.header_length = None  # int, B
		self.payload_size = None  # int, B
		self.bandwidth_prediction_bps = None  # int, 本包传输时，系统的带宽估计值
		self.size = None  # int,B
		
		self.delay = None  # ms
		self.loss_count = None  # int, 与前一个包之间的丢包个数
		self.rtt = 0.0


# ms,
def __str__(self):
	return (
		f"receive_timestamp: {self.receive_timestamp_ms}ms"
		f", send_timestamp: {self.send_timestamp_ms}ms"
		f", payload_size: {self.payload_size}B"
	)
