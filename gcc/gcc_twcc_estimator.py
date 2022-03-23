from arrival_filter import ArrivalFilter
from delay_based_bwe import DelayBasedBwe
from loss_based_bwe import LoseBasedBwe
from utils.packetRecord import PacketRecord
from .trendline_filter import TrendLineFilter


class GCC_TWCC_Estimator(object):
	def __init__(self, pktRecord: PacketRecord, lastBwe):
		self.pktRecord = pktRecord
		self.lastBwe = lastBwe
		self.rateLossController = LoseBasedBwe()
		self.rateDelayController = DelayBasedBwe()
		self.arrivalFilter = ArrivalFilter()
	
	# filter
	
	def getEstimateBandwidthByLoss(self) -> int:
		# calculate pkt loss fraction in the interval
		lossRate = self.pktRecord.calculate_loss_ratio()
		return self.rateLossController.lossBasedBwe(lossRate, self.lastBwe)
	
	def getEstimateBandwidthByDelay(self) -> int:
		# go to arrival filter
		delta_ms, group_complete_time = self.arrivalFilter.process(self.pktRecord.pkt_stats_list)
		
		# set filter
		tlf = TrendLineFilter(self.arrivalFilter.getFirstGroupCompleteTime())
		trendLineEstimated = tlf.updateTrendLine(delta_ms, group_complete_time)
	
	# overuse detector
