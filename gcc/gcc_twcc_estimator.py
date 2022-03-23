from utils.packetRecord import PacketRecord
from loss_based_bwe import LoseBasedBwe
from delay_based_bwe import DelayBasedBwe
from arrival_filter import ArrivalFilter

class GCC_TWCC_Estimator(object):
	def __init__(self, pktRecord: PacketRecord, lastBwe):
		
		self.pktRecord = pktRecord
		self.lastBwe = lastBwe
		self.rateLossController = LoseBasedBwe()
		self.rateDelayController = DelayBasedBwe()
		self.arrivalFilter = ArrivalFilter()
	
	def getEstimateBandwidthByLoss(self) -> int:
		# calculate pkt loss fraction in the interval
		lossRate = self.pktRecord.calculate_loss_ratio()
		return self.rateLossController.lossBasedBwe(lossRate, self.lastBwe)
	
	def getEstimateBandwidthByDelay(self) -> int:
		
		# go to arrival filter

		
