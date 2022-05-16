import math

from utils.my_enum import Signal

DELTA_COUNTER_MAX = 100


class kalmanV2:
	def __init__(self):
		self.slope = 8.0 / 512.0
		self.var_noise = 50.0
		self.avg_noise = 0.0
		self.E = [[100, 0], [0, 1e-1]]
		# self.E = [100, 0, 0, 1e-1]
		self.process_noise = [1e-13, 1e-3]
		
		self.history = []  # length = 60
		self.index = 0
		self.num_of_delta = 0
		
		self.offset, self.pre_offset = 0, 0
	
	def update_min_period(self, ts_delta):
		if len(self.history) == 60:
			self.history.pop(0)
		self.history.append(ts_delta)
		return min(self.history)
	
	def update_noise(self, res, ts_delta, stable_state):
		if stable_state != 0:
			return
		alpha = 0.01
		if self.num_of_delta > 300:
			alpha = 0.002
		beta = math.pow(1 - alpha, ts_delta * 30.0 / 1000.0)
		
		self.avg_noise = beta * self.avg_noise + (1 - beta) * res
		self.var_noise = beta * self.var_noise + (1 - beta) * (self.avg_noise - res) * (self.avg_noise - res)
		
		if self.var_noise < 1:
			self.var_noise = 1
	
	def update(self, delayDelta, ts_delta, size_delta, state):
		min_period = self.update_min_period(ts_delta)
		self.num_of_delta += 1
		if self.num_of_delta > DELTA_COUNTER_MAX:
			self.num_of_delta = DELTA_COUNTER_MAX
		
		# self.E[0] += self.process_noise[0]
		# self.E[3] += self.process_noise[1]
		self.E[0][0] += self.process_noise[0];
		self.E[1][1] += self.process_noise[1];
		
		if state == Signal.OVER_USE and self.offset < self.pre_offset or state == Signal.UNDER_USE and self.offset > self.pre_offset:
			self.E[1][1] += 10 * self.process_noise[1]
		
		h = [size_delta, 1.0]
		Eh = [
			self.E[0][0] * h[0] + self.E[0][1] * h[1],
			self.E[1][0] * h[0] + self.E[1][1] * h[1]
		]
		
		res = delayDelta - self.slope * h[0] - self.offset
		
		if state == Signal.NORMAL:
			in_stable_state = 0
		else:
			in_stable_state = -1
		
		max_res = 3.0 * math.sqrt(self.var_noise)
		
		if math.fabs(res) < max_res:
			self.update_noise(res, min_period, in_stable_state)
		else:
			if res < 0:
				self.update_noise(-1 * max_res, min_period, in_stable_state)
			else:
				self.update_noise(max_res, min_period, in_stable_state)
		
		denom = self.var_noise + h[0] * Eh[0] + h[1] * Eh[1]
		
		K = [
			Eh[0] / denom, Eh[1] / denom
		]
		
		IKh = [
			[1.0 - K[0] * h[0], -1 * K[0] * h[1]], [-1 * K[1] * h[0], 1.0 - K[1] * h[1]]
		]
		
		e00 = self.E[0][0]
		e01 = self.E[0][1]
		
		self.E[0][0] = e00 * IKh[0][0] + self.E[1][0] * IKh[0][1]
		self.E[0][1] = e01 * IKh[0][0] + self.E[1][1] * IKh[0][1]
		self.E[1][0] = e00 * IKh[1][0] + self.E[1][0] * IKh[1][1]
		self.E[1][1] = e01 * IKh[1][0] + self.E[1][1] * IKh[1][1]
		
		# positive_semi_definite = (self.E[0][0] + self.E[1][1]) >= 0 and (self.E[0][0] * self.E[1][1] - self.E[0][1] * \
		#                                                                  self.E[1][0]) >= 0 and self.E[0][0] >= 0
		# if positive_semi_definite is False:
		
		self.slope = self.slope + K[0] * res
		self.pre_offset = self.offset
		self.offset = self.offset + K[1] * res
	
	def run(self, delayDelta, sendDelta, sizeDelta, state):
		for index in range(len(delayDelta)):
			self.update(delayDelta[index], sendDelta[index], sizeDelta[index], state)
		
		return self.offset, self.num_of_delta,
