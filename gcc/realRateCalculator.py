from utils.packetInfo import PacketInfo


class RealRateCalculator:
	def __init__(self):
		self.windowSize = 0.5  # s，[0.5,1]; 估算实际码率的窗口长度
		self.rateHat = 0  # current incoming rate
		
		self.sumBits = 0
		self.startTimeStamp = 0
	
	def onReceive(self, pkt: PacketInfo):
		if self.startTimeStamp == 0:
			self.startTimeStamp = pkt.receive_timestamp
		if self.startTimeStamp + self.windowSize * 1000 > pkt.receive_timestamp:
			self.sumBits += (pkt.payload_size + pkt.header_length + pkt.padding_length) * 8
		else:
			self.rateHat = (self.sumBits / (pkt.receive_timestamp - self.startTimeStamp)) * 1000
