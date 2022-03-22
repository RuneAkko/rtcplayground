class GCC_TWCC_Estimator(object):
	def __init__(self):
		"""
		pacing burst time interval
		ms
		一般认为一次 burst 发出的rtp pkg 就是一帧数据，属于一个 pkg group
		"""
		self.burstInterval = 5
	
	def report_states(self, stats: dict):
		pass
	
	def get_estimated_bandwidth(self) -> int:
		pass
