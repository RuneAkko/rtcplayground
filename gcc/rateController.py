from utils.enumState import State


class RateController:
	def __init__(self):
		self.rateHatWindowSize = 0.5  # s，[0.5,1]
		"""
		另外的实现里，使用如下参数，待探究：
		#define k_initial_rate_wnd_ms 500
		#define k_rate_wnd_ms 150
		"""
		self.rateHat = 0  #
	
	def updateRateHat(self):
		pass
	
	def aimdControl(self, state: State, currentIntervalIncomingBytes, nowTime, firstPktArrivalTime):
		"""
		
		:param firstPktArrivalTime:
		:param nowTime:
		:param currentIntervalIncomingBytes:
		:param state:
		:return:
		"""
		currentIntervalIncomingRate = currentIntervalIncomingBytes * 8 / (nowTime - firstPktArrivalTime)
		currentIntervalIncomingRate *= 1000  # bits per second
	
	def increase(self) -> int:
		pass
	
	def decrease(self) -> int:
		pass
