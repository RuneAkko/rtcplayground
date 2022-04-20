from utils.my_enum import Signal


class AdaptiveThreshold:
	"""
	initializes a new adaptiveThreshold with default
	values taken from draft-ietf-rmcat-gcc-02
	"""
	
	def __init__(self, gamma=12.5, up=0.01, down=0.00018, min=6, max=600):
		self.thresholdGamma = gamma  # ms
		self.KUp = up
		self.KDown = down
		self.GammaMin = min
		self.GammaMax = max
		
		self.lastUpdateTime = -1
		self.nowTime = -1  # group arrival time
		self.maxDeltaTime = 100  # ms
		
		self.lastEstimateDuration = 0
	
	def compare(self, estimateDuration) -> Signal:
		
		result = Signal.NORMAL
		if estimateDuration > self.thresholdGamma:
			result = Signal.OVER_USE
		if estimateDuration < (-1) * self.thresholdGamma:
			result = Signal.UNDER_USE
		
		self.updateGamma(estimateDuration)
		return result
	
	def updateGamma(self, estimate):
		if self.lastUpdateTime == -1:
			self.lastUpdateTime = self.nowTime
		
		absEstimateDuration = abs(estimate)
		if absEstimateDuration > self.thresholdGamma + 15:
			self.lastUpdateTime = self.nowTime
			return
		
		k = self.KUp
		if absEstimateDuration < self.thresholdGamma:
			k = self.KDown
		
		deltaTime = min(self.nowTime - self.lastUpdateTime, self.maxDeltaTime)
		self.thresholdGamma += k * deltaTime * (absEstimateDuration - self.thresholdGamma)
		
		self.thresholdGamma = max(self.thresholdGamma, self.GammaMin)
		self.thresholdGamma = min(self.thresholdGamma, self.GammaMax)
		
		self.lastUpdateTime = self.nowTime
