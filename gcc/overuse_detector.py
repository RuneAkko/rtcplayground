from utils.enumSignal import Signal
import time


class OveruseDetector:
	def __init__(self):
		self.thresholdGamma = 12.5  # ms, according to rfc
		self.overuse_time_th = 10  # ms, at least time for trigger overuse signal
		self.first_detect_overuse_time = None  #
		self.K_up = 0.01  # gamma up rate
		self.K_down = 0.00018  # gamma down rate
	
	def overuseDetect(self, deltaTime, estimateM):
		"""
		
		:param deltaTime:
		:param estimateM:
		:return:
		"""
		#
		if estimateM > self.thresholdGamma:
			if self.first_detect_overuse_time is None:
				self.first_detect_overuse_time = int(time.time() * 1000)  # ms, 当前时间
			now = int(time.time() * 1000)
	
	def __updateGamma(self, ):
		pass
