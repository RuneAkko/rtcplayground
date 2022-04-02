#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import glob
import os
import random
import sys

import numpy as np

from gcc.main_estimator import mainEstimator
from gym import spaces

sys.path.append(os.path.join(
	os.path.dirname(os.path.abspath(__file__)), "gym"))

import alphartc_gym

UNIT_M = 1000000
MAX_BANDWIDTH_MBPS = 8
MIN_BANDWIDTH_MBPS = 0.01
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
		
		self.lastEstimatorTs = 0
	
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
	
	# 模拟器返回网络情况
	def test(self, targetRate, stepNum):
		# action: log to linear
		bandwidth_prediction = log_to_linear(targetRate)
		
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
	
	def calculateNetQos(self):
		recv_rate = self.ruleEstimator.pktsRecord.calculate_receiving_rate(
			interval=self.step_time)
		delay = self.ruleEstimator.pktsRecord.calculate_average_delay(
			interval=self.step_time)
		loss = self.ruleEstimator.pktsRecord.calculate_loss_ratio(
			interval=self.step_time)
		lastGccBwe = self.ruleEstimator.pktsRecord.calculate_latest_prediction()
		return recv_rate, delay, loss, lastGccBwe
	
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
