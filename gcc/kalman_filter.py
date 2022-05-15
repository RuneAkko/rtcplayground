import math

chi = 0.001


class kalman:
	def __init__(self):
		self.gain = 0
		self.estimate = 0  # ms
		self.processUncertainty = 1 * 10 ^ -3
		self.estimateError = 0.1
		self.measurementUncertainty = 0.01
		
		self.useTime = 0
	
	def reset(self):
		self.gain = 0
		self.estimate = 0  # ms
		self.processUncertainty = 1 * 10 ^ -3
		self.estimateError = 0.1
		self.measurementUncertainty = 0.01
		
		self.useTime = 0
	
	def updateEstimate(self, measurement):
		z = measurement - self.estimate
		
		alpha = pow(
			(1 - chi), 30.0 / (1000.0 * 5)
		)
		root = math.sqrt(
			self.measurementUncertainty
		)
		root3 = 3 * root
		
		if z > root3:
			self.measurementUncertainty = max(
				alpha * self.measurementUncertainty + (1 - alpha) * root3 * root3, 1
			)
		self.measurementUncertainty = max(
			alpha * self.measurementUncertainty + (1 - alpha) * z * z, 1
		)
		
		estimateUncertainty = self.estimateError + self.processUncertainty
		self.gain = estimateUncertainty / (estimateUncertainty + self.measurementUncertainty)
		
		self.estimate += self.gain * z  # ms
		self.estimateError = (1 - self.gain) * self.measurementUncertainty
	
	def run(self, delayDeltas, currentTime):
		self.useTime += currentTime
		
		for ele in delayDeltas:
			self.updateEstimate(ele)
		
		# if self.useTime > 100:
		# 	self.trainReset()
		
		return self.estimate
