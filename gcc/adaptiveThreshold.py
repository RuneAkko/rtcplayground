from utils.enumSignal import Signal


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
		self.comparedNums = 0  # gamma 与 estimate 比较次数
	
	def compare(self, estimate, deltaTime):
		self.comparedNums += 1
		if self.comparedNums < 2:
			return Signal.NORMAL
