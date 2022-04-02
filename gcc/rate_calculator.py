from utils.info import pktInfo


class rateCalculator:
	"""
	以实际收到的包，估算(下行)带宽；以 window size 内的平均码率作为瞬时码率
	"""
	
	def __init__(self):
		"""
		另外的实现里，使用如下参数，待探究：
		#define k_initial_rate_wnd_ms 500
		#define k_rate_wnd_ms 150
		"""
		self.windowSize = 0.5 * 1000  # ms，[0.5,1] second; 估算实际码率的时间窗口长度
		self.rateHat = 0  # current incoming rate, int, bps
		
		self.sumBytes = 0  # B
		self.history = []  # list of tmpPkts
	
	def update(self, pkt: pktInfo):
		tmpPkt = {
			"size": pkt.size,
			"arrival": pkt.receive_timestamp_ms,
		}
		
		self.history.append(tmpPkt)
		self.sumBytes += tmpPkt["size"]
		
		deadTime = tmpPkt["arrival"] - self.windowSize
		
		delIndex = 0
		for ele in self.history:
			if ele["arrival"] >= deadTime:
				break
			delIndex += 1
			self.sumBytes -= ele["size"]
		
		self.history = self.history[delIndex:]
		
		if len(self.history) == 0:
			self.rateHat = 0
			return
		
		deltaTime = tmpPkt["arrival"] - self.history[0]["arrival"]
		if deltaTime == 0:
			self.rateHat = self.sumBytes * 8
			return
		
		self.rateHat = self.sumBytes * 8 / deltaTime * 1000  # bps
