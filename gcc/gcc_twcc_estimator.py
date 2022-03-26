from arrival_filter import ArrivalFilter
from delay_based_bwe import DelayBasedBwe
from loss_based_bwe import LoseBasedBwe
from utils.packetRecord import PacketRecord
from .overuse_detector import OveruseDetector
from .rateController import RateController
from .realRateCalculator import RealRateCalculator
from .rttEstimator import RttEstimator
from .stateMachine import StateMachine
from .trendline_filter import TrendLineFilter


class GCC_TWCC_Estimator(object):
	def __init__(self, pktRecord: PacketRecord, lastBwe):
		self.pktRecord = pktRecord
		self.lastBwe = lastBwe
		self.minGroupNum = 60  # up-bound group num
		
		#
		self.totalGroupNum = 0
		
		#
		self.rateLossController = LoseBasedBwe()
		
		#
		self.rateDelayController = DelayBasedBwe()
		self.arrivalFilter = ArrivalFilter()
		self.overUseDetector = OveruseDetector()
		self.stateMachine = StateMachine()
		self.rateController = RateController()
		self.realRateCalculator = RealRateCalculator()
		self.rttEstimator = RttEstimator()
		self.now = None
		
		#
		self.currentIntervalRate = 0
	
	def getEstimateBandwidthByLoss(self) -> int:
		# calculate pkt loss fraction in the interval
		lossRate = self.pktRecord.calculate_loss_ratio()
		return self.rateLossController.lossBasedBwe(lossRate, self.lastBwe)
	
	def getEstimateBandwidthByDelay(self) -> int:
		# activate arrival filter
		delta_ms, group_complete_time = self.arrivalFilter.process(self.pktRecord.pkt_stats_list)
		
		# set now time stamp
		self.now = self.arrivalFilter.getLastGroupCompleteTime()
		
		# set filter
		tlf = TrendLineFilter(self.arrivalFilter.getFirstGroupCompleteTime())
		
		# return has multi threshold gain
		trendLineEstimated = tlf.updateTrendLine(delta_ms, group_complete_time)
		
		# gradient 没变化，带宽估计不变
		if trendLineEstimated == 0:
			return self.lastBwe
		
		# 估计时延：估计delay斜率*单位时间数，最长考虑 60 个单位时间
		#
		estimateDelayDuration = trendLineEstimated * min(self.arrivalFilter.getGroupNum(), self.minGroupNum)
		
		# 从本 interval 第一个包发出，到最后一个包发出的时间
		currentIntervalDuration = self.arrivalFilter.getcurrentIntervalDuration()
		
		# 开始 over detect
		self.totalGroupNum += self.arrivalFilter.getGroupNum()
		self.overUseDetector.totalGroupNum = self.totalGroupNum
		
		s = OveruseDetector.overuseDetect(currentIntervalDuration, estimateDelayDuration, self.now)
		
		# state transition
		state = self.stateMachine.transition(s)
		
		# aimd control rate
		
		rate = self.rateController.aimdControl(state, self.realRateCalculator.rateHat, self.now, None,
		                                       self.rttEstimator.rtt)
