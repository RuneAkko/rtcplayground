import numpy as np


class TrendLineFilter:
	def __init__(self, window_size=20, smoothing_alpha=0.9, threshold_gain=1.0):
		"""
		使用最小二乘估计求解线性回归,将斜率作为 delay gradient 的滤波值。
		
		当前版本的线性回归滤波器部署在发送端，原有版本，采样粒度是 rtcp feedback 报文。
		本实验环境为在接收端测算码率。（需要魔改）。
		魔改版本，直接使用 group 分组粒度。
		"""
		self.windowSize = window_size  # 参考的样本窗口大小，20个 inter-group 的 acc delay。
		self.smoothingAlpha = smoothing_alpha  #
		self.thresholdGain = threshold_gain  #
		
		self.accumulatedDelay = 0
		self.smoothedDelay = 0
		
		self.groupNum = 0
		
		self.firstGroupTs = 0  # 本interval的第一个group完成时间
		
		# sample point: (abs arrival time,smoothed acc delay)
		self.sampleList = []
		
		self.trendLine = 0.0  # 是一个很小的值
	
	def updateTrendLine(self, deltaTimes, arrivalTimes) -> float:
		"""
		:param deltaTimes: n 个 group 的 n-1 个 delay 变化间隔
		:param arrivalTimes: 第2-n个group的组到达时间
		:return:
		"""
		if self.firstGroupTs == 0:
			self.firstGroupTs = arrivalTimes[0]
		# 对 delay 进行指数滑动平均
		# 添加样本点
		for index in range(0, len(deltaTimes)):
			newAccumulatedDelay = self.accumulatedDelay + deltaTimes[index]
			newSmoothedDelay = self.smoothingAlpha * self.smoothedDelay + (
					1 - self.smoothingAlpha) * newAccumulatedDelay
			
			self.accumulatedDelay = newAccumulatedDelay
			self.smoothingAlpha = newSmoothedDelay
			
			sample = [arrivalTimes[index] - self.firstGroupTs, newSmoothedDelay]
			self.sampleList.append(sample)
		
		# todo: 估计 delay gradient 只用 windowsSize * burstInterval 时间内(0.1s)的数据，丢弃多余的
		if len(self.sampleList) >= self.windowSize:
			self.trendLine = self._linearFit()
		return float(self.trendLine * self.thresholdGain)
	
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
			return float(numerator / denominator)
		else:
			return 0.0
