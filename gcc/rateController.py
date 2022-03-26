import math

from utils.enumState import State


class RateController:
	def __init__(self):
		"""
		另外的实现里，使用如下参数，待探究：
		#define k_initial_rate_wnd_ms 500
		#define k_rate_wnd_ms 150
		"""
		self.lastRTT = None
		self.rateHat = 0  #
		
		self.rateAverage = 0
		self.rateAverageVar = 0
		self.rateAverageStd = 0
		
		# self.maxRate = 0
		# self.minRate = 0
		self.lastTargetRate = 0
		self.lastRateUpdateTime = 0
		self.nowTime = 0
		
		self.decreaseFactor = 0.85
		self.increaseFactor = 1.05
	
	def _updateRateHatAverageWithEMA(self, measureRate):
		alpha = 0.95
		"""
		rateHat(i) = rateHat(i-1) + alpha * (measureRate - rateHat(i-1))
		var(i) = (1-alpha)*alpha*(measureRat-rateHat(i-1))^2 + (1-alpha)*var(i-1)
		"""
		if self.rateAverage == 0:
			self.rateAverage = measureRate
		else:
			x = measureRate - self.rateAverage
			self.rateAverage += alpha * x
			self.rateAverageVar = (1 - alpha) * (self.rateAverageVar + alpha * x * x)
			self.rateAverageStd = math.sqrt(self.rateAverageVar)
	
	def expectedPktSizeBits(self) -> int:
		# 假设每秒30帧
		bitsPerFrame = self.lastTargetRate / 30
		#
		pktsPerFrame = math.ceil(bitsPerFrame / (1200 * 8))
		#
		avgPktSizeBits = bitsPerFrame / pktsPerFrame
		return avgPktSizeBits
	
	def aimdControl(self, state: State, rateHat, nowTime, firstPktArrivalTime, rtt) -> int:
		"""
		
		:param rtt:
		:param rateHat: bits per second
		:param firstPktArrivalTime:
		:param nowTime: ms
		:param state:
		:return:
		"""
		self._updateRateHatAverageWithEMA(rateHat)
		self.rateHat = rateHat
		self.lastRTT = rtt
		self.nowTime = nowTime
		
		if state == State.INCREASE:
			return self.increase()
		elif state == State.DECREASE:
			return self.decrease()
		else:
			return self.lastTargetRate
	
	def increase(self) -> int:
		
		if self.rateAverage > 0 and (self.rateAverage - 3 * self.rateAverageStd) <= self.rateHat <= (
				self.rateAverage + 3 * self.rateAverageStd):
			# additive scheme
			responseTime = 100 + self.lastRTT
			alpha = 0.5 * min(1, self.lastRateUpdateTime / responseTime)
			self.lastTargetRate = self.lastTargetRate + max(1000, alpha * self.expectedPktSizeBits())
			self.lastRateUpdateTime = self.nowTime
			return self.lastTargetRate
		eta = self.increaseFactor ** min(self.lastRateUpdateTime / 1000, 1)
		self.lastTargetRate = eta * self.lastTargetRate
		
		if self.lastTargetRate > 1.5 * self.rateHat:
			self.lastTargetRate = 1.5 * self.rateHat
		
		self.lastRateUpdateTime = self.nowTime
		return self.lastTargetRate
	
	def decrease(self) -> int:
		self.lastTargetRate = self.decreaseFactor * self.rateHat
		self.lastRateUpdateTime = self.nowTime
		return self.lastTargetRate
