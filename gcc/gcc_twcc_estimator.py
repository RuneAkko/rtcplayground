from arrival_filter import ArrivalFilter
from delay_based_bwe import DelayBasedBwe
from loss_based_bwe import LoseBasedBwe
from utils.packetRecord import PacketRecord
from .overuse_detector import OveruseDetector
from .trendline_filter import TrendLineFilter


class GCC_TWCC_Estimator(object):
	def __init__(self, pktRecord: PacketRecord, lastBwe):
		self.pktRecord = pktRecord
		self.lastBwe = lastBwe
		self.minGroupNum = 60  # up-bound group num
		self.rateLossController = LoseBasedBwe()
		self.rateDelayController = DelayBasedBwe()
		self.arrivalFilter = ArrivalFilter()
		self.overUseDetector = OveruseDetector()
		self.now = None
	
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
		trendLineEstimated = tlf.updateTrendLine(delta_ms, group_complete_time)
		
		# gradient 没变化，带宽估计不变
		if trendLineEstimated == 0:
			return self.lastBwe
		
		# 估计时延：估计delay斜率*单位时间数
		#
		estimateDelayDuration = trendLineEstimated * min(self.arrivalFilter.getGroupNum(), self.minGroupNum)
		
		# 从本 interval 第一个包发出到最后一个包发出的时间
		currentIntervalDuration = self.arrivalFilter.getcurrentIntervalDuration()
		
		OveruseDetector.overuseDetect(currentIntervalDuration, estimateDelayDuration, self.now)

# overuse detector
