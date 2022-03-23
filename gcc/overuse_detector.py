from utils.enumSignal import Signal
from .adaptiveThreshold import AdaptiveThreshold


class OveruseDetector:
	def __init__(self):
		self.overuse_time_th = 10  # ms, at least time for trigger overuse signal
		self.overuseDuration = 0  # ms,
		self.lastSignal = Signal.NORMAL
		self.adaptiveThreshold = AdaptiveThreshold()
	
	def overuseDetect(self, currentIntervalDuration, estimateDelayDuration, nowTime) -> Signal:
		nailTime = currentIntervalDuration
		
		#
		gamma = self.adaptiveThreshold.thresholdGamma
		
		# above condition
		if estimateDelayDuration > gamma:
			if estimateDelayDuration - gamma <= 15:
				self.__updateGamma(deltaTime, self.KUp, estimateDelayDuration)
			
			if currentGroupArrivalTime - lastGroupArrivalTime >= self.overuse_time_th:
				return Signal.OVER_USE
			return Signal.NORMAL
