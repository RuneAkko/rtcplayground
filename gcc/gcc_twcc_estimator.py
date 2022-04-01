import copy
import logging

from utils.record import pktRecord
from .arrival_filter import ArrivalFilter
from .delay_based_bwe import DelayBasedBwe
from .loss_based_bwe import LoseBasedBwe
from .overuse_detector import OveruseDetector
from .rate_calculator import rateCalculator
from .rate_controller import RateController
from .rtt_calculator import rttCalculator
from .state_machine import StateMachine
from .trendline_filter import TrendLineFilter

MaxGroupNum = 60  # 每个 interval 纳入考虑的最大范围；pkt group 的个数；
GroupBurstInterval = 5  # ms, pacer 一次性发送 5 ms 内的包，认为是一个 pkt group;


class GCC(object):
	def __init__(self, predictionBandwidth):
		self.predictionBandwidth = predictionBandwidth
		self.maxGroupNum = MaxGroupNum
		
		self.record = None
		self.currentTimestamp = -1.0  # the last pkt arrival time of this interval,ms
		self.firstGroupArrivalTime = 0  # the first group's last pkt arrival time ,ms
		
		self.totalGroupNum = 0  #
		
		self.currentIntervalRate = 0
		
		#
		self.rateLossController = LoseBasedBwe(self.predictionBandwidth)
		
		#
		self.rateDelayController = DelayBasedBwe()
		
		# delay module component
		self.arrivalFilter = ArrivalFilter(GroupBurstInterval)
		self.overUseDetector = OveruseDetector()
		self.stateMachine = StateMachine()
		self.rateController = RateController()
		
		self.rateCalculator = rateCalculator()
		
		self.rttCalculator = rttCalculator()
	
	def setIntervalState(self, record: pktRecord):
		self.record = copy.deepcopy(record)
	
	def getEstimateBandwidth(self) -> int:
		loss_rate = self.getEstimateBandwidthByLoss()
		delay_rate = self.getEstimateBandwidthByDelay()
		self.predictionBandwidth = min(
			loss_rate, delay_rate
		)
		logging.info("[in this interval] loss-rate is [%s], delay-rate is [%s]", loss_rate, delay_rate)
		return self.predictionBandwidth
	
	def getEstimateBandwidthByLoss(self) -> int:
		lossRate = self.record.calculate_loss_ratio()
		logging.info("[in this interval] loss-ratio is [%s]", lossRate)
		return self.rateLossController.lossBasedBwe(lossRate)
	
	def getEstimateBandwidthByDelay(self):
		self.arrivalFilter.preFilter(self.record.pkts)
		self.totalGroupNum += self.arrivalFilter.groupNum
		logging.info("[in this interval] group num is [%s]", self.arrivalFilter.groupNum)
		if self.arrivalFilter.groupNum < 2:
			return self.predictionBandwidth
		
		delayDelta, arrivalTs = self.arrivalFilter.measured_groupDelay_deltas()
		logging.info("[in this interval] delayDelta from group is [%s]", delayDelta)
		logging.info("[in this interval] arrivalTs from group is [%s]", arrivalTs)
		
		tlf = TrendLineFilter()
		tlf.firstGroupTs = self.arrivalFilter.pktGroups[0].arrivalTs
		
		queueDelayDelta = tlf.updateTrendLine(delayDelta, arrivalTs)
		logging.info("[in this interval] queueDelayDelta is [%s]", queueDelayDelta)
		
		# gradient 没变化，带宽估计不变
		if queueDelayDelta == 0:
			return self.predictionBandwidth
		
		# 估计时延：估计delay斜率*单位时间数，最长考虑 60 个单位时间
		#
		estimateQueueDelayDuration = queueDelayDelta * \
		                             min(self.arrivalFilter.groupNum, self.maxGroupNum)
		
		# # 从本 interval 第一个包发出，到最后一个包发出的时间
		currentIntervalDuration = self.arrivalFilter.pktGroups[0]
		
		self.overUseDetector.totalGroupNum = self.totalGroupNum
		
		s = OveruseDetector.detect(estimateQueueDelayDuration, self.currentTimestamp)
		logging.info("[in this interval] adaptiveThresholdGamma is [%s]",
		             self.overUseDetector.adaptiveThreshold.thresholdGamma)
		# state transition
		state = self.stateMachine.transition(s)
		logging.info("[in this interval] rate state is [%s]",
		             state)
		# aimd control rate
		rate = self.rateController.aimdControl(state, self.rateCalculator.rateHat, self.currentTimestamp,
		                                       self.rttCalculator.rtt)
		logging.info("[in this interval] now real rate is [%s]",
		             self.rateCalculator.rateHat)
		logging.info("[in this interval] now real rtt is [%s]",
		             self.rttCalculator.rtt)
		return rate
