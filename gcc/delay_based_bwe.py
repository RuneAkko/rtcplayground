class DelayBasedBwe:
	def __init__(self):
		self.decreaseFactor = 0.85
		self.increaseFactor = 1.05
		self.lastBwe = 0
		self.recentlyRate = 0
		self.state = None  # delay based rate controller system state

# def increase(self) -> int:
# 	self.state = State.INCREASE
# 	return int(self.increaseFactor * self.lastBwe)
#
# def decrease(self) -> int:
# 	self.state = State.DECREASE
# 	return int(self.decreaseFactor * self.recentlyRate)
#
# def hold(self) -> int:
# 	self.state = State.HOLD
# 	return self.lastBwe
#
# def delayBasedBwe(self, lastBwe, signal, recentlyRate) -> int:
# 	"""
#
# 	:param recentlyRate:
# 	:param lastBwe:
# 	:param signal: 从 overuse detector 发出的信号
# 	:param recentlyRate: 最近 500 ms 内的平均接收码率
# 	:return:
# 	"""
# 	assert lastBwe >= 0
# 	assert recentlyRate >= 0
#
# 	self.lastBwe = lastBwe
# 	self.recentlyRate = recentlyRate
