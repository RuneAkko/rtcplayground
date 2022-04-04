#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time

import numpy as np

from gcc.main_estimator import mainEstimator
from geminiGCC.main_estimator import mainGeminiEstimator, get_time_ms
from utils.utilBackup.packet_info import PacketInfo
from utils.utilBackup.packet_record import PacketRecord

sys.path.append(os.path.join(
	os.path.dirname(os.path.abspath(__file__)), "gym"))

import alphartc_gym

UNIT_M = 1000000
# MAX_BANDWIDTH_MBPS = 8
MAX_BANDWIDTH_MBPS = 20
# MIN_BANDWIDTH_MBPS = 0.01
MIN_BANDWIDTH_MBPS = 0.08
LOG_MAX_BANDWIDTH_MBPS = np.log(MAX_BANDWIDTH_MBPS)
LOG_MIN_BANDWIDTH_MBPS = np.log(MIN_BANDWIDTH_MBPS)

INIT_BANDWIDTH = 3000 * 1000  # 3m bps


def liner_to_log(value):
	# from 10kbps~8Mbps to 0~1
	value = np.clip(value / UNIT_M, MIN_BANDWIDTH_MBPS, MAX_BANDWIDTH_MBPS)
	log_value = np.log(value)
	return (log_value - LOG_MIN_BANDWIDTH_MBPS) / (LOG_MAX_BANDWIDTH_MBPS - LOG_MIN_BANDWIDTH_MBPS)


def log_to_linear(value):
	# from 0~1 to 10kbps to 8Mbps
	value = np.clip(value, 0, 1)
	log_bwe = value * (LOG_MAX_BANDWIDTH_MBPS -
	                   LOG_MIN_BANDWIDTH_MBPS) + LOG_MIN_BANDWIDTH_MBPS
	return np.exp(log_bwe) * UNIT_M


def get_time_ms():
	return int(time.time() * 1000)


class GymEnv:
	def __init__(self, step_time=60):
		self.packet_record = PacketRecord()
		self.gym_env = None
		self.step_time = step_time  # 仿真环境 report pkt stat 的间隔, ms
		
		self.ruleEstimator = mainEstimator(INIT_BANDWIDTH)
		self.geminiEstimator = mainGeminiEstimator(INIT_BANDWIDTH)
		
		self.lastEstimatorTs = 0
		self.lastBwe = INIT_BANDWIDTH
	
	# 设置仿真环境使用的trace
	def setAlphaRtcGym(self, trace):
		self.gym_env = alphartc_gym.Gym()
		self.gym_env.reset(trace_path=trace,
		                   report_interval_ms=self.step_time,
		                   duration_time_ms=0)
	
	# 用于测试拥塞控制算法在特定 trace 上的表现
	# 接收估计带宽，执行拥塞控制，返回下一个 step interval pkts
	# v1 使用 own-gcc
	def testV1(self, targetRate):
		# action: log to linear
		# bandwidth_prediction = log_to_linear(targetRate)
		
		packet_list, done = self.gym_env.step(targetRate)
		
		for pkt in packet_list:
			self.ruleEstimator.report_states(pkt)
		
		next_targetRate = self.ruleEstimator.predictionBandwidth
		
		if len(packet_list) > 0:
			nowTs = self.ruleEstimator.gcc.currentTimestamp
			# 调用带宽估计间隔
			if (nowTs - self.lastEstimatorTs) >= 200:
				self.lastEstimatorTs = nowTs
				next_targetRate = self.ruleEstimator.get_estimated_bandwidth()
		if next_targetRate != 0:
			self.lastBwe = next_targetRate
		qos1, qos2, qos3, qos4 = self.calculateNetQosV1()
		
		return self.lastBwe, done, qos1, qos2, qos3, qos4, packet_list
	
	# 用于测试拥塞控制算法在特定 trace 上的表现
	# 接收估计带宽，执行拥塞控制，返回下一个 step interval pkts
	# v2 使用 gemini-gcc
	def testV2(self, targetRate):
		packet_list, done = self.gym_env.step(targetRate)
		
		next_targetRate = 0
		if len(packet_list) > 0:
			now_ts = get_time_ms() - self.geminiEstimator.first_time
			self.geminiEstimator.gcc_ack_bitrate.ack_estimator_incoming(packet_list)
			result = self.geminiEstimator.gcc_rate_controller.delay_bwe_incoming(
				packet_list, self.geminiEstimator.gcc_ack_bitrate.ack_estimator_bitrate_bps(),
				now_ts)
			next_targetRate = result.bitrate
		if next_targetRate != 0:
			self.lastBwe = next_targetRate
		
		for pkt in packet_list:
			packet_info = PacketInfo()
			packet_info.payload_type = pkt["payload_type"]
			packet_info.ssrc = pkt["ssrc"]
			packet_info.sequence_number = pkt["sequence_number"]
			packet_info.send_timestamp = pkt["send_time_ms"]
			packet_info.receive_timestamp = pkt["arrival_time_ms"]
			packet_info.padding_length = pkt["padding_length"]
			packet_info.header_length = pkt["header_length"]
			packet_info.payload_size = pkt["payload_size"]
			packet_info.bandwidth_prediction = self.lastBwe
			self.packet_record.on_receive(packet_info)
		qos1, qos2, qos3, qos4 = self.calculateNetQosV2()
		return self.lastBwe, done, qos1, qos2, qos3, qos4, packet_list
	
	def calculateNetQosV1(self):
		recv_rate = self.ruleEstimator.pktsRecord.calculate_receiving_rate(
			interval=self.step_time)
		delay = self.ruleEstimator.pktsRecord.calculate_average_delay(
			interval=self.step_time)
		loss = self.ruleEstimator.pktsRecord.calculate_loss_ratio(
			interval=self.step_time)
		lastGccBwe = self.ruleEstimator.pktsRecord.calculate_latest_prediction()
		return recv_rate, delay, loss, lastGccBwe
	
	def calculateNetQosV2(self):
		recv_rate = self.packet_record.calculate_receiving_rate(
			interval=self.step_time)
		delay = self.packet_record.calculate_average_delay(
			interval=self.step_time)
		loss = self.packet_record.calculate_loss_ratio(
			interval=self.step_time)
		lastGccBwe = self.packet_record.calculate_latest_prediction()
		return recv_rate, delay, loss, lastGccBwe
