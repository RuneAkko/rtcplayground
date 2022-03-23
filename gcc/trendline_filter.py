"""
当前版本的滤波器
使用最小二乘估计求解线性回归
"""
import numpy as np


class TrendLineFilter:
	def __init__(self, firstGroupCompleteTime, window_size=20, smoothing_coef=0.9, threshold_gain=1.0):
		self.windowSize = window_size
		self.smoothingAlpha = smoothing_coef
		self.thresholdGain = threshold_gain
		
		self.accumulatedDelay = 0
		self.smoothedDelay = 0
		
		self.groupNum = 0
		
		self.firstGroupCompleteTime = firstGroupCompleteTime
		
		# sample point: (time,smoothed delay)
		self.sampleList = []
		
		self.trendLine = 0
	
	def updateTrendLine(self, deltaTimes, arrivalTimes) -> int:
		"""
		
		:param deltaTimes: n 个 group 的 n-1 个 delay 变化间隔
		:param arrivalTimes: 第2-n 个 group 的组到达时间
		:return:
		"""
		
		# 对 delay 进行指数滑动平均
		# 添加样本点
		for index in range(0, len(deltaTimes)):
			newAccumulatedDelay = self.accumulatedDelay + deltaTimes[index]
			newSmoothedDelay = self.smoothingAlpha * self.smoothedDelay + (
					1 - self.smoothingAlpha) * newAccumulatedDelay
			
			self.accumulatedDelay = newAccumulatedDelay
			self.smoothingAlpha = newSmoothedDelay
			
			sample = [arrivalTimes[index] - self.firstGroupCompleteTime, newSmoothedDelay]
			self.sampleList.append(sample)
		
		# todo: 估计 delay gradient 只用 windowsSize * burstInterval 时间内(0.1s)的数据，丢弃多余的
		if len(self.sampleList) >= self.windowSize:
			self.trendLine = self._linearFit()
		return self.trendLine * self.thresholdGain
	
	def _linearFit(self):
		x_list = self.sampleList[0][:]
		y_list = self.sampleList[1][:]
		x_avg = np.mean(x_list)
		y_avg = np.mean(y_list)
		numerator = np.sum(
			list(
				map(lambda x: (x[0] - x_avg) * (x[1] - y_avg),
				    zip(x_list, y_list))))
		denominator = np.sum(
			list(
				map(lambda x: (x[0] - x_avg) * (x[0] - x_avg),
				    zip(x_list, y_list))))
		if denominator != 0:
			return numerator / denominator
		else:
			return 0
