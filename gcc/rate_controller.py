import math

from utils.my_enum import State, aimdType


class RateController:
	def __init__(self, targetRate):
		"""

		"""
		self.lastRTT = None
		self.rateHat = 0  # bps
		self.rateHatKbps = 0  # kbps
		
		self.average_max_rate_kbps = -1.0
		self.average_max_rate_kbps_var = 0.4
		self.average_max_rate_kbps_std = math.sqrt(self.average_max_rate_kbps_var)
		
		# self.maxRate = 0
		# self.minRate = 0
		self.lastTargetRate = targetRate  # bps
		
		self.lastRateUpdateTime = 0
		self.nowTime = 0
		
		self.decreaseFactor = 0.85
		self.increaseFactor = 1.05
		
		self.type = aimdType.MAX_UNKNOWN
	
	def _updateRateHatAverageWithEMA(self, measureRateKbps):
		alpha = 0.05
		"""
		rateHat(i) = rateHat(i-1) + alpha * (measureRateKbps - rateHat(i-1))
		var(i) = (1-alpha)*alpha*(measureRat-rateHat(i-1))^2 + (1-alpha)*var(i-1)
		"""
		if self.average_max_rate_kbps == -1.0:
			self.average_max_rate_kbps = measureRateKbps
		else:
			self.average_max_rate_kbps = (1 - alpha) * self.average_max_rate_kbps + alpha * measureRateKbps
		
		err = self.average_max_rate_kbps - measureRateKbps
		norm = max(self.average_max_rate_kbps, 1.0)
		
		self.average_max_rate_kbps_var = (1 - alpha) * self.average_max_rate_kbps_var + alpha * err * err / norm
		"""
		// 0.4 ~= 14 kbit/s at 500 kbit/s
        // 2.5f ~= 35 kbit/s at 500 kbit/s
        deviation_kbps_ = rtc::SafeClamp(deviation_kbps_, 0.4f, 2.5f);
		"""
		if self.average_max_rate_kbps_var < 0.4:
			self.average_max_rate_kbps_var = 0.4
		if self.average_max_rate_kbps_var > 2.5:
			self.average_max_rate_kbps_var = 2.5
		
		self.average_max_rate_kbps_std = math.sqrt(self.average_max_rate_kbps_var)
	
	def aimdControl(self, state: State, rateHat, nowTime, rtt) -> float:
		"""
		
		:param rtt:
		:param rateHat: bits per second
		:param nowTime: ms
		:param state:
		:return:
		"""
		self.rateHat = rateHat  # bps
		self.rateHatKbps = self.rateHat / 1000  # kbps
		self.lastRTT = rtt
		self.nowTime = nowTime
		self._updateRateHatAverageWithEMA(self.rateHatKbps)
		
		if state == State.INCREASE:
			return self.increase()
		elif state == State.DECREASE:
			return self.decrease()
		else:
			return self.lastTargetRate
	
	def increase(self) -> float:
		
		result = self.lastTargetRate
		if self.average_max_rate_kbps >= 0 and self.rateHatKbps > self.average_max_rate_kbps + 3 * self.average_max_rate_kbps_std:
			# 离链路可用带宽依然遥远，
			self.type = aimdType.MAX_UNKNOWN
			self.average_max_rate_kbps = -1.0
		
		if self.type == aimdType.NEAR_MAX:
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
				result = (self.decreaseFactor * self.average_max_rate_kbps * 1000)
			result = min(result, self.lastTargetRate)
		
		self.type = "Additive"
		
		if self.rateHatKbps < self.average_max_rate_kbps - 3 * self.average_max_rate_kbps_std:
			self.average_max_rate_kbps = -1.0
		self._updateRateHatAverageWithEMA(self.rateHatKbps)
		
		self.lastRateUpdateTime = self.nowTime
		self.lastTargetRate = result
		return self.lastTargetRate
	
	def multiType(self):
		eta = self.increaseFactor ** min((self.nowTime - self.lastRateUpdateTime) / 1000.0, 1.0)
		result = max((eta - 1) * self.lastTargetRate, 1000.0)
		return result
	
	def additiveType(self):
		# additive scheme
		# return bps
		responseTime = 100 + self.lastRTT
		alpha = 0.5 * min(1.0, (self.nowTime - self.lastRateUpdateTime) / responseTime)
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
