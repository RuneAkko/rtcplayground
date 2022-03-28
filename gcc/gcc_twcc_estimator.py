from arrival_filter import ArrivalFilter
from delay_based_bwe import DelayBasedBwe
from loss_based_bwe import LoseBasedBwe
from utils.record import pktRecord
from .overuse_detector import OveruseDetector
from .rateController import RateController
from .rate_calculator import rateCalculator
from .rtt_calculator import rttCalculator
from .stateMachine import StateMachine
from .trendline_filter import TrendLineFilter

MaxGroupNum = 60  # 每个 interval 纳入考虑的最大范围；pkt group 的个数；


class GCC(object):
	def __init__(self, record: pktRecord, predictionBandwidth):
		self.record = record
		self.predictionBandwidth = predictionBandwidth
		self.currentTimestamp = 0  # the last pkt arrival time of this interval,ms
		
		self.maxGroupNum = MaxGroupNum
		self.totalGroupNum = 0
		
		#
		self.rateLossController = LoseBasedBwe(self.predictionBandwidth)
		
		#
		self.rateDelayController = DelayBasedBwe()
		self.arrivalFilter = ArrivalFilter()
		self.overUseDetector = OveruseDetector()
		self.stateMachine = StateMachine()
		self.rateController = RateController()
		
		self.rateCalculator = rateCalculator()
		
		self.rttCalculator = rttCalculator()
		
		#
		self.currentIntervalRate = 0
	
	def getEstimateBandwidth(self) -> int:
		self.predictionBandwidth = min(
			self.getEstimateBandwidthByDelay(),
			self.getEstimateBandwidthByLoss()
		)
		return self.predictionBandwidth
	
	def getEstimateBandwidthByLoss(self) -> int:
		lossRate = self.record.calculate_loss_ratio()
		return self.rateLossController.lossBasedBwe(lossRate)
	
	def getEstimateBandwidthByDelay(self) -> int:
		# activate arrival filter
		delta_ms, group_complete_time = self.arrivalFilter.process(self.record.pkts)
		
		# set currentTimestamp time stamp
		self.currentTimestamp = self.arrivalFilter.getLastGroupCompleteTime()
		
		# set filter
		tlf = TrendLineFilter(self.arrivalFilter.getFirstGroupCompleteTime())
		
		# return has multi threshold gain
		trendLineEstimated = tlf.updateTrendLine(delta_ms, group_complete_time)
		
		# gradient 没变化，带宽估计不变
		if trendLineEstimated == 0:
			return self.lastBwe
		
		# 估计时延：估计delay斜率*单位时间数，最长考虑 60 个单位时间
		#
		estimateDelayDuration = trendLineEstimated * min(self.arrivalFilter.getGroupNum(), self.maxGroupNum)
		
		# 从本 interval 第一个包发出，到最后一个包发出的时间
		currentIntervalDuration = self.arrivalFilter.getcurrentIntervalDuration()
		
		# 开始 over detect
		self.totalGroupNum += self.arrivalFilter.getGroupNum()
		self.overUseDetector.totalGroupNum = self.totalGroupNum
		
		s = OveruseDetector.overuseDetect(currentIntervalDuration, estimateDelayDuration, self.currentTimestamp)
		
		# state transition
		state = self.stateMachine.transition(s)
		
		# aimd control rate
		
		rate = self.rateController.aimdControl(state, self.rateCalculator.rateHat, self.currentTimestamp, None,
		                                       self.rttCalculator.rtt)
		
		return rate
