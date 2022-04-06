from utils.my_enum import Signal
from .adaptive_threshold import AdaptiveThreshold


class OveruseDetector:
	def __init__(self):
		self.overuse_time_th = 10  # ms, 触发 overuse signal 至少需要持续的时间
		self.lastSignal = Signal.NORMAL  # 上次 detect 得到的信号
		
		self.overuseDuration = -1  # ms, 认定为 overuse stage 已经持续的时间
		self.overuseContinueCounter = 0
		self.lastEstimateDelayDuration = 0
		self.adaptiveThreshold = AdaptiveThreshold()
		self.lastUpdate = 0
		self.totalGroupNum = 0
	
	def detect(self, estimateDelayDuration, nowTime) -> Signal:
		
		# start up
		if self.totalGroupNum < 2:
			self.lastSignal = Signal.NORMAL
			return Signal.NORMAL
		
		currentIntervalDuration = nowTime - self.lastUpdate
		self.lastUpdate = nowTime
		self.adaptiveThreshold.nowTime = nowTime
		
		nowSignal = self.adaptiveThreshold.compare(estimateDelayDuration)
		
		finalSignal = Signal.NORMAL
		
		# above
		if nowSignal == Signal.OVER_USE:
			if self.overuseDuration == -1:
				self.overuseDuration = currentIntervalDuration / 2
			else:
				self.overuseDuration += currentIntervalDuration
			
			self.overuseContinueCounter += 1
			
			if self.overuseDuration > self.overuse_time_th and self.overuseContinueCounter > 1:
				if estimateDelayDuration >= self.lastEstimateDelayDuration:
					finalSignal = Signal.OVER_USE
					self.overuseDuration = 0
					self.overuseContinueCounter = 0
		
		# under
		if nowSignal == Signal.UNDER_USE:
			self.overuseDuration = -1
			self.overuseContinueCounter = 0
			finalSignal = Signal.UNDER_USE
		
		# between
		if nowSignal == Signal.NORMAL:
			self.overuseDuration = -1
			self.overuseContinueCounter = 0
			finalSignal = Signal.NORMAL
		
		self.lastEstimateDelayDuration = estimateDelayDuration
		
		return finalSignal
