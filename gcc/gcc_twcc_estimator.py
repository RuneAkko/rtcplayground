import copy
import logging

from utils.record import pktRecord
from .arrival_filter import ArrivalFilter
from .loss_based_bwe import LoseBasedBwe
from .overuse_detector import OveruseDetector
from .rate_calculator import rateCalculator
from .rate_controller import RateController
from .rtt_calculator import rttCalculator
from .state_machine import StateMachine
from .trendline_filter import TrendLineFilter
from .kalman_filter import kalman

MaxGroupNum = 60  # 每个 interval 纳入考虑的最大范围；pkt group 的个数；
GroupBurstInterval = 5  # ms, pacer 一次性发送 5 ms 内的包，认为是一个 pkt group;


class GCC(object):
	def __init__(self, predictionBandwidth, filterType="kal"):
		self.predictionBandwidth = predictionBandwidth  # bps
		self.predictionDelayBwe = predictionBandwidth  # bps
		self.predictionLossBwe = predictionBandwidth  # bps
		self.minGroupNum = MaxGroupNum
		
		self.record = None
		self.currentTimestamp = -1.0  # the last pkt arrival time of this interval,ms
		
		self.firstGroupArrivalTime = 0  # the first group's last pkt arrival time ,ms
		
		self.totalGroupNum = 0  #
		
		self.currentIntervalRate = 0
		
		#
		self.rateLossController = LoseBasedBwe(self.predictionBandwidth)
		
		#
		# self.rateDelayController = DelayBasedBwe()
		
		# delay module component
		self.arrivalFilter = ArrivalFilter(GroupBurstInterval)
		self.tlf = TrendLineFilter()
		self.klm = kalman()
		self.filterType = filterType
		
		self.overUseDetector = OveruseDetector()
		self.stateMachine = StateMachine()
		self.rateController = RateController(self.predictionBandwidth)
		
		self.rateCalculator = rateCalculator()
		
		self.rttCalculator = rttCalculator()
		
		self.inflightGroups = []
		
		#
		self.queueDelayDelta = 0
	
	def setIntervalState(self, record: pktRecord):
		self.record = copy.deepcopy(record)
	
	def getEstimateBandwidth(self) -> int:
		# loss_rate = self.getEstimateBandwidthByLoss()
		delay_rate = self.getEstimateBandwidthByDelay()
		self.predictionBandwidth = min(
			delay_rate, delay_rate
		)
		# self.predictionBandwidth = delay_rate
		logging.info("[in this interval] delay-rate is [%s] mbps",
		             delay_rate / 1000000)
		# self.rateLossController.bwe = self.predictionBandwidth
		return self.predictionBandwidth
	
	def getEstimateBandwidthByLoss(self) -> int:
		lossRate = self.record.calculate_loss_ratio()
		logging.info("[in this interval] loss-ratio is [%s]", lossRate)
		return self.rateLossController.lossBasedBwe(lossRate)
	
	def getEstimateBandwidthByDelay(self):
		self.arrivalFilter.preFilter(self.record.pkts)
		self.totalGroupNum += self.arrivalFilter.groupNum
		
		logging.info("[in this interval] group num is [%s]", self.arrivalFilter.groupNum)
		
		if self.arrivalFilter.groupNum + len(self.inflightGroups) < 2:
			self.inflightGroups += copy.deepcopy(self.arrivalFilter.pktGroups)
			return self.predictionBandwidth
		
		self.arrivalFilter.pktGroups = self.inflightGroups + self.arrivalFilter.pktGroups
		self.arrivalFilter.groupNum = len(self.arrivalFilter.pktGroups)
		self.inflightGroups = []
		
		delayDelta, arrivalTs = self.arrivalFilter.measured_groupDelay_deltas()
		logging.info("[in this interval] delayDelta from group is [%s]", delayDelta)
		
		if self.filterType == "tlf":
			queueDelayDelta = self.tlf.updateTrendLine(delayDelta, arrivalTs)
		else:
			queueDelayDelta = self.klm.run(delayDelta, self.currentTimestamp)
		
		if queueDelayDelta is None:
			queueDelayDelta = 0
		
		if queueDelayDelta is None:
			queueDelayDelta = 0
		
		# gradient 没变化，带宽估计不变
		# if queueDelayDelta == 0:
		# 	return self.predictionBandwidth
		
		if self.filterType == "tlf":
			# 估计时延：估计delay斜率*单位时间数，最长考虑 60 个单位时间
			estimateQueueDelayDuration = queueDelayDelta * \
			                             min(self.tlf.numCount, self.minGroupNum)
			logging.info("estimateQueueDelayDuration [%s] = queueDelayDelta [%s] * numCount[%s]",
			             estimateQueueDelayDuration, queueDelayDelta, min(self.tlf.numCount, self.minGroupNum))
			self.queueDelayDelta = estimateQueueDelayDuration
		else:
			estimateQueueDelayDuration = queueDelayDelta
			self.queueDelayDelta = estimateQueueDelayDuration
		# # # 从本 interval 第一个包发出，到最后一个包发出的时间
		# currentIntervalDuration = self.arrivalFilter.pktGroups[0]
		
		self.overUseDetector.totalGroupNum = self.totalGroupNum
		
		signal = self.overUseDetector.detect(estimateQueueDelayDuration, self.currentTimestamp)
		logging.info("signal is [%s]",
		             signal)
		logging.info("adaptiveThresholdGamma is [%s]",
		             self.overUseDetector.adaptiveThreshold.thresholdGamma)
		# pre_state transition
		state = self.stateMachine.transition(signal)
		# logging.info("[in this interval] pre_state is [%s]",
		#              state)
		# aimd control rate
		rate = self.rateController.aimdControl(state, self.rateCalculator.rateHat, self.currentTimestamp,
		                                       self.rttCalculator.rtt)
		logging.info("[in this interval] rateHat is [%s]mbps",
		             self.rateCalculator.rateHat / 1000000)
		logging.info("[in this interval] now real rtt is [%s]",
		             self.rttCalculator.rtt)
		logging.info("[in this interval] aimd control rate is [%s] mbps", rate / 1000000)
		self.predictionBandwidth = rate
		return rate
