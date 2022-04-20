"""
constants from
https://datatracker.ietf.org/doc/html/draft-ietf-rmcat-gcc-02#section-6
"""


class LoseBasedBwe:
	"""
	理论上，loss control 应在 gym 发送端；
	在 recv 端实现的 loss control may be shadowed;
	loss 的运行间隔是 RTCP report 的间隔；
	不妨按照每个 estimate interval 来估算 loss
	"""
	
	def __init__(self, bwe):
		self.increaseLossThreshold = 0.02
		self.increaseFactor = 1.05
		self.decreaseLossThreshold = 0.1
		
		self.bwe = bwe  # bps
	
	def lossBasedBwe(self, loss) -> int:
		assert loss >= 0
		
		if loss > self.decreaseLossThreshold:
			self.bwe = self.bwe * (1 - 0.5 * loss)
		elif loss < self.increaseLossThreshold:
			self.bwe = self.increaseFactor * self.bwe
		return self.bwe
