#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import glob
import os
import random
import sys
import time

import numpy as np

from gcc.main_estimator import mainEstimator
from geminiGCC.main_estimator import mainGeminiEstimator, get_time_ms
from gym import spaces
from utils.utilBackup.packet_info import PacketInfo
from utils.utilBackup.packet_record import PacketRecord

sys.path.append(os.path.join(
	os.path.dirname(os.path.abspath(__file__)), "gym"))

import alphartc_gym

UNIT_M = 1000000
MAX_BANDWIDTH_MBPS = 10
MIN_BANDWIDTH_MBPS = 0.01
LOG_MAX_BANDWIDTH_MBPS = np.log(MAX_BANDWIDTH_MBPS)
LOG_MIN_BANDWIDTH_MBPS = np.log(MIN_BANDWIDTH_MBPS)

INIT_BANDWIDTH = 300 * 1000  # 3 kbps


def liner_to_log(value):
	"""
	
	:param value: bps
	:return: 0-1
	"""
	value = np.clip(value / UNIT_M, MIN_BANDWIDTH_MBPS, MAX_BANDWIDTH_MBPS)
	log_value = np.log(value)
	return (log_value - LOG_MIN_BANDWIDTH_MBPS) / (LOG_MAX_BANDWIDTH_MBPS - LOG_MIN_BANDWIDTH_MBPS)


def log_to_linear(value):
	"""
	
	:param value: 0-1
	:return: bps
	"""
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
		
		self.ruleEstimator = mainEstimator(INIT_BANDWIDTH, MAX_BANDWIDTH_MBPS, MIN_BANDWIDTH_MBPS)
		self.geminiEstimator = mainGeminiEstimator(INIT_BANDWIDTH)
		
		self.lastEstimatorTs = 0
		self.lastBwe = INIT_BANDWIDTH
		
		# ========================= drl attr ======================#
		
		self.action_space = spaces.Box(
			low=0.0, high=1.0, shape=(1,), dtype=np.float64
		)
		self.observation_space = spaces.Box(
			low=np.array([0.0, 0.0, 0.0, 0.0]),
			high=np.array([1.0, 1.0, 1.0, 1.0]),
			dtype=np.float64)
		
		self.train_trace_set = None
		
		self.state_dim = 5
	
	def setAlphaRtcGym(self, trace):
		"""
		设置仿真环境使用的trace
		:param trace: trace file path
		:return:
		"""
		self.gym_env = alphartc_gym.Gym()
		self.gym_env.reset(trace_path=trace,
		                   report_interval_ms=self.step_time,
		                   duration_time_ms=0)
	
	def testV1(self, targetRate):
		"""
		用于测试拥塞控制算法在特定 trace 上的表现
		接收估计带宽，执行拥塞控制，返回下一个 step interval pkts
		v1 使用 own-gcc
		:param targetRate: bps
		:return:
		"""
		
		packet_list, done = self.gym_env.step(targetRate)
		
		for pkt in packet_list:
			self.ruleEstimator.report_states(pkt)
		
		next_targetRate = self.ruleEstimator.predictionBandwidth
		
		if len(packet_list) > 0:
			# nowTs = self.ruleEstimator.gcc.currentTimestamp
			# 调用带宽估计间隔
			# if (nowTs - self.lastEstimatorTs) >= 1000:
			# 	self.lastEstimatorTs = nowTs
			next_targetRate = self.ruleEstimator.get_estimated_bandwidth()
		if next_targetRate != 0:
			self.lastBwe = next_targetRate
		qos1, qos2, qos3, qos4 = self.calculateNetQosV1()
		
		return self.lastBwe, done, qos1, qos2, qos3, qos4, packet_list
	
	def testV2(self, targetRate):
		"""
		用于测试拥塞控制算法在特定 trace 上的表现
		接收估计带宽，执行拥塞控制，返回下一个 step interval pkts
		v2 使用 gemini-gcc
		:param targetRate: bps
		:return:
		"""
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
	
	def setTraces(self, path):
		self.train_trace_set = glob.glob(f'{path}/*.json', recursive=True)
	
	def reset(self):
		"""
		
		:return: state [5]
		"""
		self.packet_record = PacketRecord()
		self.packet_record.reset()
		self.gym_env = alphartc_gym.Gym()
		trace_path = random.choice(self.train_trace_set)
		print(trace_path)
		self.gym_env.reset(trace_path=trace_path,
		                   report_interval_ms=self.step_time,
		                   duration_time_ms=0)
		self.lastBwe = INIT_BANDWIDTH
		return [0.0 for _ in range(self.state_dim)]
	
	def step(self, action):
		"""
		
		:param action: 0.0-1.0
		:return:
		"""
		bandwidth_prediction_bps = log_to_linear(action)
		if self.lastBwe == INIT_BANDWIDTH:
			self.lastBwe = bandwidth_prediction_bps
		# run the action
		packet_list, done = self.gym_env.step(bandwidth_prediction_bps)
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
			packet_info.bandwidth_prediction = bandwidth_prediction_bps
			self.packet_record.on_receive(packet_info)
		
		# calculate state
		# in this step/interval , state value
		states = []
		receiving_rate = self.packet_record.calculate_receiving_rate(interval=self.step_time)
		states.append(liner_to_log(receiving_rate))  # 0.0-1.0
		
		delay = self.packet_record.calculate_average_delay(interval=self.step_time)
		states.append(min(delay / 1000, 2) / 2)  # second , with no base delay
		
		loss_ratio = self.packet_record.calculate_loss_ratio(interval=self.step_time)
		states.append(loss_ratio)  # 0.0-1.0
		
		latest_prediction = self.packet_record.calculate_latest_prediction()
		states.append(liner_to_log(latest_prediction))  # 0.0-1.0
		
		delta_prediction = abs((bandwidth_prediction_bps - self.lastBwe
		                        )).squeeze().numpy()  # 原来的是[[x]]现在先压平然后转换成numpy
		states.append(liner_to_log(delta_prediction))
		
		self.lastBwe = bandwidth_prediction_bps
		
		# reward function: gemini
		# reward = states[
		# 	         0] - 1.5 * states[1] - 1.5 * states[2] - 0.02 * states[4]
		
		# # reward : my
		# reward = 4 * states[
		# 	0] - 1 * states[1] - 4 * states[2]
		# 

		# reward microsoft:
		reward = 0.6*np.log(4*receiving_rate/1000000+1) - delay*2/1000- 10 *loss_ratio
		return states, reward, done, {}
