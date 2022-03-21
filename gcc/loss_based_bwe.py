"""
constants from
https://datatracker.ietf.org/doc/html/draft-ietf-rmcat-gcc-02#section-6
"""


class LoseBasedBwe:
	def __init__(self):
		self.increaseLossThreshold = 0.02
		self.increaseFactor = 1.05
		self.decreaseLossThreshold = 0.1
	
	def lossBasedBwe(self, loss, lastBwe) -> int:
		assert loss >= 0
		assert lastBwe >= 0
		
		rate = lastBwe
		if loss > self.decreaseLossThreshold:
			rate = lastBwe * (1 - 0.5 * lastBwe)
		elif loss < self.increaseLossThreshold:
			rate = self.increaseFactor * lastBwe
		return rate
