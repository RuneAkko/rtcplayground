class DelayBasedBwe:
	def __init__(self):
		self.decreaseFactor = 0.85
		self.increaseFactor = 1.05
		self.switch = {
			"Increase": self.increase,
			"Decrease": self.decrease,
			"Hold": self.hold
		}
		self.lastBwe = 0
		self.recentlyRate = 0
	
	def increase(self) -> int:
		return self.increaseFactor * self.lastBwe
	
	def decrease(self) -> int:
		return self.decreaseFactor * self.recentlyRate
	
	def hold(self) -> int:
		return self.lastBwe
	
	def delayBasedBwe(self, lastBwe, signal, recentlyRate) -> int:
		"""
		
		:param recentlyRate:
		:param lastBwe:
		:param signal:
		:param recentlyRate: 最近 500 ms 内的平均接收码率
		:return:
		"""
		assert lastBwe >= 0
		assert recentlyRate >= 0
		assert signal in self.switch
		self.lastBwe = lastBwe
		self.recentlyRate = recentlyRate
		return self.switch.get(signal)
