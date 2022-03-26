from utils.packetInfo import PacketInfo


class RttEstimator:
	def __init__(self):
		self.rtt = None  # ms
	
	def calRTT(self, pkt: PacketInfo):
		self.rtt = (pkt.receive_timestamp - pkt.send_timestamp) * 2
