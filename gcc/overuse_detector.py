from utils.enumSignal import Signal


class OveruseDetector:
	def __init__(self):
		self.thresholdGamma = 12.5  # ms, according to rfc
		self.overuse_time_th = 10  # ms, at least time for trigger overuse signal
		self.first_detect_overuse_time = None  #
		self.KUp = 0.01  # gamma up rate
		self.KDown = 0.00018  # gamma down rate
		self.lastSignal = Signal.NORMAL
	
	def overuseDetect(self, lastGroupArrivalTime, currentGroupArrivalTime, estimateM) -> Signal:
		deltaTime = currentGroupArrivalTime - lastGroupArrivalTime
		
		if estimateM > self.thresholdGamma:
			if estimateM - self.thresholdGamma <= 15:
				self.__updateGamma(deltaTime, self.KUp, estimateM)
			
			if self.first_detect_overuse_time is None:
				self.first_detect_overuse_time = currentGroupArrivalTime  # ms, 当前时间
			
			if currentGroupArrivalTime - lastGroupArrivalTime >= self.overuse_time_th:
				return Signal.OVER_USE
			return Signal.NORMAL
	
	def __updateGamma(self, deltaTime, K, M):
		self.thresholdGamma = self.thresholdGamma + deltaTime * K * (abs(M) - self.thresholdGamma)
