#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import glob
import math
import os
import random
import sys
import time

import numpy as np

from gcc.main_estimator import GccNativeEstimator
from hrccGCC.BandwidthEstimator_gcc import HrccGCCEstimator
from hrccGCCKalman.BandwidthEstimator_gcc import HrccGCCEstimatorWithKalman
from geminiGCC.main_estimator import GccGeminiEstimator, get_time_ms
from gym import spaces
from utils.utilBackup.packet_info import PacketInfo
from utils.utilBackup.packet_record import PacketRecord
from utils.trace import Trace
from unsafetyDetector import unsafety_detector
from utils.qosReport import QosReport

sys.path.append(os.path.join(
	os.path.dirname(os.path.abspath(__file__)), "gym"))

import alphartc_gym

UNIT_M = 1000000
MAX_BANDWIDTH_MBPS = 20
MIN_BANDWIDTH_MBPS = 0.08
LOG_MAX_BANDWIDTH_MBPS = np.log(MAX_BANDWIDTH_MBPS)
LOG_MIN_BANDWIDTH_MBPS = np.log(MIN_BANDWIDTH_MBPS)

INIT_BANDWIDTH = 300 * 1000  # unit: bps; 300kbps


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
	def __init__(self, step_time=60, state_dim=6, k_up=0.0087, k_down=0.039):
		self.packet_record = PacketRecord()
		
		# ========================= cc algo attr ==================== #
		filter_type = ["tlf", "kal", "kalv2", "none"]
		self.gccEstimator = GccNativeEstimator(INIT_BANDWIDTH, MAX_BANDWIDTH_MBPS, MIN_BANDWIDTH_MBPS, filter_type[-1])
		self.geminiEstimator = GccGeminiEstimator(INIT_BANDWIDTH)
		self.hrccEstimator = HrccGCCEstimator(k_up=k_up, k_down=k_down)
		self.hrccEstimatorWithKal = HrccGCCEstimatorWithKalman(k_up=k_up, k_down=k_down)
		# ========================= common attr ==================== #
		
		self.gymProcess = None
		self.step_time = step_time  # 仿真环境 report pkt stat 的间隔, ms
		self.current_trace = Trace()
		self.report = QosReport()
		
		self.lastEstimatorTs = 0
		self.lastBwe = INIT_BANDWIDTH
		
		# ========================= drl attr ====================== #
		
		self.action_space = spaces.Box(
			low=0.0, high=1.0, shape=(1,), dtype=np.float64
		)
		self.observation_space = spaces.Box(
			low=np.array([0.0, 0.0, 0.0, 0.0]),
			high=np.array([1.0, 1.0, 1.0, 1.0]),
			dtype=np.float64)
		
		self.train_trace_set = None
		
		self.state_dim = state_dim
		
		# ========================== hybird attr ============================== #
		self.safety = 1
		self.lastChoice = "drl"
		self.unsafe_detector = unsafety_detector()
		self.hy_gcc = 0
	
	def updatePktRecord(self, packet_list):
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
	
	def updateDrlMetric(self, delta_prediction):
		state = []  # recv; delay; loss; last-bwe; delta-bwe
		state.append(liner_to_log(self.report.receiveRate[-1]))
		
		state.append(min(self.report.delay[-1] / 1000.0, 1))
		state.append(self.report.loss[-1])
		state.append(liner_to_log(self.packet_record.calculate_latest_prediction()))
		state.append(liner_to_log(delta_prediction))
		
		# reward function
		# reward = states[0] - 2.5 * states[1] - 5 * states[2] - 0.02 * states[4]
		reward = state[
			         0] - 1.5 * state[1] - 1.5 * state[2] - 0.02 * state[4]
		self.report.reward.append(reward)
		return state
	
	def init4Test(self, trace_path):
		"""
		"""
		self.current_trace.path = trace_path
		self.current_trace.readTraceFile()
		self.gymProcess = alphartc_gym.Gym()
		self.gymProcess.reset(trace_path=trace_path,
		                      report_interval_ms=self.step_time,
		                      duration_time_ms=0)
		return self.current_trace
	
	def init4Train(self, path):
		self.train_trace_set = glob.glob(path, recursive=True)
	
	def trainReset(self):
		"""
		
		"""
		self.packet_record = PacketRecord()
		self.packet_record.reset()
		self.lastBwe = INIT_BANDWIDTH
		
		# ======================== #
		trace_path = random.choice(self.train_trace_set)
		print(trace_path)
		self.current_trace.traceFilePath = trace_path
		self.current_trace.readTraceFile()
		
		self.gymProcess = alphartc_gym.Gym()
		self.gymProcess.reset(trace_path=trace_path,
		                      report_interval_ms=self.step_time,
		                      duration_time_ms=0)
		return [0.0 for _ in range(self.state_dim)]
	
	def testHrccGcc(self, targetRate):
		packet_list, done = self.gymProcess.step(targetRate)
		self.updatePktRecord(packet_list)
		if len(packet_list) > 0:
			for pkt in packet_list:
				self.hrccEstimator.report_states(pkt)
		next_targetRate, _ = self.hrccEstimator.get_estimated_bandwidth()
		if next_targetRate != 0:
			self.lastBwe = next_targetRate
		self.calculateNetQos()
		# ===============================================
		self.report.queueDelayDelta.append(self.hrccEstimator.prober_queueDelayDelta)
		self.report.queueDelayDelta_m.append(self.hrccEstimator.prober_queueDelayDelta_m)
		self.report.gamma.append(self.hrccEstimator.gamma1)
		# ===============================================
		return self.lastBwe, done, packet_list
	
	def testHrccGccWithKal(self, targetRate):
		packet_list, done = self.gymProcess.step(targetRate)
		self.updatePktRecord(packet_list)
		if len(packet_list) > 0:
			for pkt in packet_list:
				self.hrccEstimatorWithKal.report_states(pkt)
		next_targetRate, _ = self.hrccEstimatorWithKal.get_estimated_bandwidth()
		if next_targetRate != 0:
			self.lastBwe = next_targetRate
		self.calculateNetQos()
		# ===============================================
		self.report.queueDelayDelta.append(self.hrccEstimatorWithKal.prober_queueDelayDelta)
		self.report.queueDelayDelta_m.append(self.hrccEstimatorWithKal.prober_queueDelayDelta_m)
		self.report.gamma.append(self.hrccEstimatorWithKal.gamma1)
		# ===============================================
		
		return self.lastBwe, done, packet_list
	
	def testGccNative(self, targetRate):
		"""
		用于测试拥塞控制算法在特定 trace 上的表现
		接收估计带宽，执行拥塞控制，返回下一个 testDrl interval pkts
		使用 gcc-native
		:param targetRate: bps
		"""
		
		packet_list, done = self.gymProcess.step(targetRate)
		self.updatePktRecord(packet_list)
		for pkt in packet_list:
			self.gccEstimator.report_states(pkt)
		
		next_targetRate = self.gccEstimator.predictionBandwidth
		
		if len(packet_list) > 0:
			# nowTs = self.gccEstimator.gcc.currentTimestamp
			# 调用带宽估计间隔
			# if (nowTs - self.lastEstimatorTs) >= 1000:
			# 	self.lastEstimatorTs = nowTs
			next_targetRate = self.gccEstimator.get_estimated_bandwidth()
		if next_targetRate != 0:
			self.lastBwe = next_targetRate
		self.calculateNetQos()
		# =================================
		self.report.queueDelayDelta.append(self.gccEstimator.gcc.queueDelayDelta)
		self.report.gamma.append(self.gccEstimator.gcc.overUseDetector.adaptiveThreshold.thresholdGamma)
		# self.report.trend.append(self.gccEstimator.gcc.rateController.digLog)
		
		return self.lastBwe, done, packet_list
	
	def testGccGemini(self, targetRate):
		"""
		使用 gemini pure gcc
		:param targetRate: bps
		"""
		packet_list, done = self.gymProcess.step(targetRate)
		
		if len(packet_list) > 0:
			now_ts = get_time_ms() - self.geminiEstimator.first_time
			self.geminiEstimator.gcc_ack_bitrate.ack_estimator_incoming(packet_list)
			result = self.geminiEstimator.gcc_rate_controller.delay_bwe_incoming(
				packet_list, self.geminiEstimator.gcc_ack_bitrate.ack_estimator_bitrate_bps(),
				now_ts)
			if result.bitrate != 0:
				self.lastBwe = result.bitrate
		
		self.updatePktRecord(packet_list)
		self.calculateNetQos()
		
		# =================================
		self.report.queueDelayDelta.append(self.geminiEstimator.gcc_rate_controller.detector.T)
		self.report.gamma.append(self.geminiEstimator.gcc_rate_controller.trendline_estimator.trendline * 4)
		# =================================
		return self.lastBwe, done, packet_list
	
	def testDrl(self, action):
		"""
		
		:param action:
		:return:
		"""
		bandwidth_prediction_bps = log_to_linear(action)
		packet_list, done = self.gymProcess.step(bandwidth_prediction_bps)  # run the action
		if self.lastBwe == INIT_BANDWIDTH:  # drl init bwe is not 300 kbps
			self.lastBwe = bandwidth_prediction_bps
		self.updatePktRecord(packet_list)
		self.calculateNetQos()
		
		# ========= cal state =============== #
		delta_prediction = abs((bandwidth_prediction_bps - self.lastBwe
		                        )).squeeze().numpy()
		state = self.updateDrlMetric(delta_prediction)
		self.lastBwe = bandwidth_prediction_bps
		
		return state, done
	
	def calculateNetQos(self):
		recv_rate = self.packet_record.calculate_receiving_rate(
			interval=self.step_time)
		delay = self.packet_record.calculate_average_delay(
			interval=self.step_time)
		loss = self.packet_record.calculate_loss_ratio(
			interval=self.step_time)
		lastBwe = self.packet_record.calculate_latest_prediction()
		self.report.update(recv_rate, delay, loss, lastBwe)
	
	def testHy(self, action):
		bandwidth_prediction_bps = log_to_linear(action)
		
		# choose bwe
		if self.safety == 1:  # use drl action
			packet_list, done = self.gymProcess.step(bandwidth_prediction_bps)
		else:
			# use gcc action
			bwe_dl = bandwidth_prediction_bps
			bwe_gcc = self.hy_gcc
			
			bandwidth_prediction = bwe_gcc
			# change_window 未归零,
			if self.unsafe_detector.change_window != 10 and self.unsafe_detector.change_window != 0:
				window = self.unsafe_detector.change_window
				# gcc-bwe shift to drl-bwe
				bandwidth_prediction = bwe_dl * ((10 - window) / 10) + bwe_gcc * (
						window / 10)
			packet_list, done = self.gymProcess.step(bandwidth_prediction)
		
		# invoke gcc
		next_hy_gcc = 0
		if len(packet_list) > 0:
			for pkt in packet_list:
				self.hrccEstimator.report_states(pkt)
			next_hy_gcc, _ = self.hrccEstimator.get_estimated_bandwidth()
		
		if next_hy_gcc != 0:
			self.hy_gcc = next_hy_gcc
		
		if self.safety == 0:
			bandwidth_prediction_bps = self.hy_gcc
		
		if self.lastBwe == INIT_BANDWIDTH:  # drl init bwe is not 300 kbps
			self.lastBwe = bandwidth_prediction_bps
		
		self.calculateNetQos()
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
			self.unsafe_detector.receive(packet_info.receive_timestamp, packet_info.send_timestamp)
		
		if self.safety == 1:
			delta_prediction = abs((bandwidth_prediction_bps - self.lastBwe
			                        )).squeeze().numpy()  # 原来的是[[x]]现在先压平然后转换成numpy
		else:
			delta_prediction = abs((bandwidth_prediction_bps - self.lastBwe
			                        ))  # 单位是百分比
		state = self.updateDrlMetric(delta_prediction)
		self.lastBwe = bandwidth_prediction_bps
		if self.report.delay[-1] > 1000:
			self.unsafe_detector.detect_big_delay()
		self.safety = self.unsafe_detector.getState()
		return state, done
