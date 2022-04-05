import math

from utils.my_enum import State


class RateController:
	def __init__(self, targetRate):
		"""

		"""
		self.lastRTT = None
		self.rateHat = 0  # bps
		
		self.rateAverage = -1.0
		self.rateAverageVar = 0.4
		self.rateAverageStd = math.sqrt(self.rateAverageVar)
		
		# self.maxRate = 0
		# self.minRate = 0
		self.lastTargetRate = targetRate  # bps
		
		self.lastRateUpdateTime = 0
		self.nowTime = 0
		
		self.decreaseFactor = 0.85
		self.increaseFactor = 1.05
		
		self.type = "Multi"
	
	def _updateRateHatAverageWithEMA(self, measureRate):
		alpha = 0.05
		"""
		rateHat(i) = rateHat(i-1) + alpha * (measureRate - rateHat(i-1))
		var(i) = (1-alpha)*alpha*(measureRat-rateHat(i-1))^2 + (1-alpha)*var(i-1)
		"""
		if self.rateAverage == -1.0:
			self.rateAverage = measureRate
		else:
			
			self.rateAverage += (1 - alpha) * self.rateAverage + alpha * measureRate
			
			err = self.rateAverage - measureRate
			norm = max(self.rateAverage, 1.0)
			
			self.rateAverageVar = (1 - alpha) * self.rateAverageVar + alpha * err * err / norm
			"""
			// 0.4 ~= 14 kbit/s at 500 kbit/s
            // 2.5f ~= 35 kbit/s at 500 kbit/s
            deviation_kbps_ = rtc::SafeClamp(deviation_kbps_, 0.4f, 2.5f);
			"""
			if self.rateAverageVar < 0.4:
				self.rateAverageVar = 0.4
			if self.rateAverageVar > 2.5:
				self.rateAverageVar = 2.5
			
			self.rateAverageStd = math.sqrt(self.rateAverageVar)
	
	def aimdControl(self, state: State, rateHat, nowTime, rtt) -> float:
		"""
		
		:param rtt:
		:param rateHat: bits per second
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
	
	def increase(self) -> float:
		
		result = self.lastTargetRate
		if self.rateAverage >= 0 and self.rateHat > self.rateAverage + 3 * self.rateAverageStd:
			# 离链路可用带宽依然遥远，
			self.type = "Multi"
			self.rateAverage = -1.0
		
		if self.type == "Additive":
			# 靠近可用带宽上限，加性增
			result = self.lastTargetRate + self.additiveType()
		else:
			# 乘性增
			result = self.lastTargetRate + self.multiType()
		
		if result > 1.5 * self.rateHat:
			result = 1.5 * self.rateHat
		
		self.lastRateUpdateTime = self.nowTime
		self.lastTargetRate = result
		return self.lastTargetRate
	
	def decrease(self) -> float:
		result = self.decreaseFactor * self.rateHat
		if result > self.lastTargetRate:
			if self.type != "Multi":
				result = (self.decreaseFactor * self.rateAverage)
			result = min(result, self.lastTargetRate)
		
		self.type = "Additive"
		
		if self.rateHat < self.rateAverage - 3 * self.rateAverageStd:
			self.rateAverage = -1.0
		self._updateRateHatAverageWithEMA(self.rateHat)
		
		self.lastRateUpdateTime = self.nowTime
		self.lastTargetRate = result
		return self.lastTargetRate
	
	def multiType(self):
		eta = self.increaseFactor ** min((self.nowTime - self.lastRateUpdateTime) / 1000.0, 1.0)
		result = max((eta - 1) * self.lastTargetRate, 1000.0)
		return result
	
	def additiveType(self):
		# additive scheme
		responseTime = 100 + self.lastRTT
		alpha = min(1.0, (self.nowTime - self.lastRateUpdateTime) / responseTime)
		result = max(1000.0, alpha * self.expectedPktSizeBits())
		return result
	
	def expectedPktSizeBits(self) -> float:
		# 假设每秒30帧
		bitsPerFrame = self.rateHat / 30.0
		#
		pktsPerFrame = math.ceil(bitsPerFrame / (1200 * 8))
		#
		avgPktSizeBits = bitsPerFrame / pktsPerFrame
		return avgPktSizeBits
