from utils.info import pktInfo


class rttCalculator:
	def __init__(self):
		self.rtt = 0  # ms
	
	def simpleRtt(self, pkt: pktInfo):
		"""
		使用收到的最近的包的单向时延估算 round trip time
		:param pkt:
		:return:
		"""
		self.rtt = max(pkt.delay * 2, 0)
