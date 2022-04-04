#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import glob
import os
import random
import sys

import alphartc_gym.utils.packet_record
import numpy as np
from alphartc_gym.utils.packet_info import PacketInfo

from gcc.main_estimator import mainEstimator
from geminiGCC.main_estimator import mainGeminiEstimator, get_time_ms
from gym import spaces

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


class GymEnv:
	def __init__(self, step_time=60):
		self.gym_env = None
		self.step_time = step_time
		trace_dir = os.path.join(os.path.dirname(__file__), "traces")
		self.trace_set = glob.glob(f'{trace_dir}/**/*.json', recursive=True)
		self.action_space = spaces.Box(
			low=0.0, high=1.0, shape=(1,), dtype=np.float64)
		self.observation_space = spaces.Box(
			low=np.array([0.0, 0.0, 0.0, 0.0]),
			high=np.array([1.0, 1.0, 1.0, 1.0]),
			dtype=np.float64)
		self.ruleEstimator = mainEstimator()
		self.geminiEstimator = mainGeminiEstimator(self.ruleEstimator.predictionBandwidth)
		
		self.lastEstimatorTs = 0
		
		self.lastBwe = None
	
	# 模拟器返回网络情况
	def test(self, targetRate, stepNum):
		# action: log to linear
		# bandwidth_prediction = log_to_linear(targetRate)
		bandwidth_prediction = targetRate
		
		packet_list, done = self.gym_env.step(bandwidth_prediction)
		
		for pkt in packet_list:
			self.ruleEstimator.report_states(pkt)
		
		targetRate = self.ruleEstimator.predictionBandwidth
		
		if len(packet_list) > 0:
			nowTs = self.ruleEstimator.gcc.currentTimestamp
			if (nowTs - self.lastEstimatorTs) >= 200:
				self.lastEstimatorTs = nowTs
				targetRate = self.ruleEstimator.get_estimated_bandwidth()
		
		qos1, qos2, qos3, qos4 = self.calculateNetQos()
		
		return targetRate, done, qos1, qos2, qos3, qos4, packet_list
	
	def testV2(self, targetRate):
		# bandwidth_prediction = log_to_linear(targetRate)
		bandwidth_prediction = targetRate
		deltaTime = 0
		if self.geminiEstimator.last_time is None:
			self.geminiEstimator.last_time = get_time_ms()
			deltaTime = 0
		else:
			now = get_time_ms()
			deltaTime = now - self.geminiEstimator.last_time
			self.geminiEstimator.last_time = now
		
		packet_list, done = self.gym_env.step(bandwidth_prediction)
		
		gccRate = 0
		if len(packet_list) > 0:
			now_ts = get_time_ms() - self.geminiEstimator.first_time
			self.geminiEstimator.gcc_ack_bitrate.ack_estimator_incoming(packet_list)
			result = self.geminiEstimator.gcc_rate_controller.delay_bwe_incoming(
				packet_list, self.geminiEstimator.gcc_ack_bitrate.ack_estimator_bitrate_bps(),
				now_ts)
			gccRate = result.bitrate
		if gccRate != 0:
			self.lastBwe = gccRate
			bandwidth_prediction = gccRate
		
		if self.lastBwe is None:
			self.lastBwe = bandwidth_prediction
		
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
			packet_info.bandwidth_prediction = bandwidth_prediction
			self.packet_record.on_receive(packet_info)
		return bandwidth_prediction / UNIT_M
	
	def calculateNetQos(self):
		recv_rate = self.ruleEstimator.pktsRecord.calculate_receiving_rate(
			interval=self.step_time)
		delay = self.ruleEstimator.pktsRecord.calculate_average_delay(
			interval=self.step_time)
		loss = self.ruleEstimator.pktsRecord.calculate_loss_ratio(
			interval=self.step_time)
		lastGccBwe = self.ruleEstimator.pktsRecord.calculate_latest_prediction()
		return recv_rate, delay, loss, lastGccBwe
	
	# 用于 drl training
	# 重置rtc模拟环境、带宽估计器
	# 随机选择trace
	def reset(self):
		self.gym_env = alphartc_gym.Gym()
		self.gym_env.reset(trace_path=random.choice(self.trace_set),
		                   report_interval_ms=self.step_time,
		                   duration_time_ms=0)
		self.ruleEstimator = mainEstimator()
		
		return [0.0, 0.0, 0.0, 0.0]
	
	# 规则算法测试
	def set(self, testTrace):
		self.gym_env = alphartc_gym.Gym()
		self.gym_env.reset(trace_path=testTrace,
		                   report_interval_ms=self.step_time,
		                   duration_time_ms=0)
		self.ruleEstimator = mainEstimator()
	
	# 用于强化学习执行 action，返回 reward
	def step(self, action):
		# action: log to linear
		bandwidth_prediction = log_to_linear(action)
		
		# 模拟器返回网络情况
		packet_list, done = self.gym_env.step(bandwidth_prediction)
		
		for pkt in packet_list:
			self.ruleEstimator.report_states(pkt)
		
		receiving_rate, delay, loss_ratio, latest_prediction = self.calculateNetQos()
		
		# calculate state
		states = [liner_to_log(receiving_rate), min(
			delay / 1000, 1), loss_ratio, liner_to_log(latest_prediction)]
		
		# 奖励函数
		reward = states[0] - states[1] - states[2]
		return states, reward, done, {}
