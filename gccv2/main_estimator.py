from utils.info import pktInfo
from utils.my_enum import interfaceState, bbrType
from utils.record import pktRecord
from .gcc_twcc_estimator import GCC
import math
from collections import deque

BaseDelay = 200  # ms, 假设传播时延


class mainEstimatorV2(object):
	def __init__(self, initialBwe, maxBwe, minBwe):
		self.pktsRecord = pktRecord(BaseDelay)
		self.pktsRecord.reset()
		
		self.state = interfaceState.INIT
		
		self.gcc = GCC(initialBwe)
		
		# last interval value or initial value, bps, int
		self.predictionBandwidth = initialBwe
		
		self.minBwe = minBwe
		self.maxBwe = maxBwe
		
		self.stats = []
		
		# bbr need args
		self.currentR = deque(maxlen=3)
		self.currentLoss = 0
		self.minRTT = 200  # ms
		self.BDP = 0
		self.startUpGain = 2 / math.log(2)
		self.gain = [1.25, 0.75, 1, 1, 1, 1, 1, 1]
		self.gainIndex = 0
		self.bbrType = bbrType.INIT
		self.Ab = initialBwe
		self.count = 0
	
	def report_states(self, stats: dict):
		"""
		stats is a rtp pkt to a dict with the following items
		{
			"send_time_ms": uint,
			"arrival_time_ms": uint,
			"payload_type": int,
			"sequence_number": uint,
			"ssrc": int,
			"padding_length": uint,
			"header_length": uint,
			"payload_size": uint
		},
		example:
		[
			{
				'arrival_time_ms': 66113,
				'header_length': 24,
				'padding_length': 0,
				'payload_size': 1389,
				'payload_type': 126,
				'send_time_ms': 60999,
				'sequence_number': 54366,
				'ssrc': 12648429
			},
			{
				'arrival_time_ms': 66181,
				'header_length': 24,
				'padding_length': 0,
				'payload_size': 1389,
				'payload_type': 126,
				'send_time_ms': 61069,
				'sequence_number': 54411,
				'ssrc': 12648429}
		]
		"""
		if self.state == interfaceState.ESTIMATE:
			self.stats = []
		self.state = interfaceState.REPORT
		
		if len(stats) <= 0:
			return
		
		pkt_info = pktInfo()
		pkt_info.payload_type = stats["payload_type"]
		pkt_info.ssrc = stats["ssrc"]
		pkt_info.sequence_number = stats["sequence_number"]
		pkt_info.send_timestamp_ms = stats["send_time_ms"]
		pkt_info.receive_timestamp_ms = stats["arrival_time_ms"]
		pkt_info.padding_length = stats["padding_length"]
		pkt_info.header_length = stats["header_length"]
		pkt_info.payload_size = stats["payload_size"]
		
		pkt_info.size = stats["padding_length"] + \
		                stats["header_length"] + stats["payload_size"]
		
		pkt_info.bandwidth_prediction_bps = self.predictionBandwidth
		
		# todo: 确认是否应该给包加上假设的 base delay
		self.pktsRecord.on_receive(pkt_info)
		
		self.gcc.rateCalculator.update(pkt_info)
		
		self.gcc.rttCalculator.simpleRtt(self.pktsRecord.pkts[-1].delay)
		
		self.gcc.currentTimestamp = pkt_info.receive_timestamp_ms
		
		self.stats.append(stats)
	
	def get_estimated_bandwidth(self) -> int:
		if self.state == interfaceState.REPORT:
			self.state = interfaceState.ESTIMATE
		# else:
		# 	return self.predictionBandwidth
		self.updateCurrentBBRSignal()
		if self.pktsRecord.packet_num <= 0:
			return 100 * 1000
		
		self.count += 1
		if self.count >= 10:
			
			self.gcc.setIntervalState(self.pktsRecord, self.stats)
			
			if self.bbrType == bbrType.INIT and self.currentLoss <= 0.02:
				self.bbrType = bbrType.START_UP
			
			if self.bbrType == bbrType.START_UP:
				self.startUp()
				self.gcc.getEstimateBandwidth()
				self.gcc.predictionBandwidth = self.Ab
				self.predictionBandwidth = self.Ab
				return self.predictionBandwidth
			
			if self.bbrType == bbrType.RETREAT:
				if self.currentLoss >= 0.02:
					self.bbrType = bbrType.RECOVERY
				elif self.gcc.queueDelayDelta <= 0:
					self.gcc.getEstimateBandwidth()
					self.gcc.predictionBandwidth = self.Ab
					self.predictionBandwidth = self.Ab
					return self.predictionBandwidth
				else:
					self.predictionBandwidth = self.gcc.getEstimateBandwidth()
					self.bbrType = bbrType.QUIT
			
			if self.bbrType == bbrType.RECOVERY:
				self.recover()
				self.gcc.getEstimateBandwidth()
				self.gcc.predictionBandwidth = self.Ab
				self.predictionBandwidth = self.Ab
				return self.predictionBandwidth
		
		self.predictionBandwidth = self.gcc.getEstimateBandwidth()
		self.Ab = self.predictionBandwidth
		return self.predictionBandwidth
	
	def updateCurrentBBRSignal(self):
		self.currentR.append(self.pktsRecord.calculate_receiving_rate(60))
		self.currentLoss = self.pktsRecord.calculate_loss_ratio(60)
	
	def startUp(self):
		if self.currentR[2] >= self.currentR[1] and self.currentR[2] >= 1.25 * self.currentR[0]:
			if self.Ab < 3 * self.BDP:
				self.Ab = self.startUpGain * self.Ab
				self.BDP = self.currentR[2]
		else:
			self.bbrType = bbrType.RETREAT
	
	def recover(self):
		self.Ab = min(self.gain[self.gainIndex] * self.Ab, 2 * self.BDP)
		self.gainIndex += 1
		if self.gainIndex == 8:
			self.gainIndex = 0
			if self.currentR[2] >= self.currentR[0]:
				self.Ab = max(self.currentR[2], self.Ab)
				self.BDP = self.currentR[2]
			else:
				self.BDP = self.currentR[2]
				if self.gcc.queueDelayDelta > 0:
					self.bbrType = bbrType.QUIT
