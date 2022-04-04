import time
from geminiGCC.ack_bitrate_estimator import Ack_bitrate_estimator
from geminiGCC.delaybasedbwe import delay_base_bwe


def get_time_ms():
	return int(time.time() * 1000)


class mainGeminiEstimator:
	def __init__(self, initBwe):
		self.latest_bandwidth = initBwe
		self.first_time = get_time_ms()
		self.gcc_rate_controller = delay_base_bwe()
		self.gcc_rate_controller.set_time(self.first_time)
		self.gcc_rate_controller.set_start_bitrate(self.latest_bandwidth)
		self.gcc_ack_bitrate = Ack_bitrate_estimator()
