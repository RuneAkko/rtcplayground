import matplotlib.pyplot as plt
import numpy as np

from utils.qosReport import QosReport, Curve, Figure
import statsmodels.api as sm


class CdfCurve:
	def __init__(self, args: dict):
		"""
		name:
		color:
		shape:
		:param args:
		:return:
		"""
		self.attr = args
		self.x = []
		self.y = []
	
	# self.data = []
	
	def update(self, data):
		ecdf = sm.distributions.ECDF(data)
		self.y = np.linspace(min(data), max(data))
		self.x = ecdf(self.y)
	
	def yAxisUnit(self, unit):
		if unit == "kbps":
			self.y = [tmp / 1000 for tmp in self.y]


def cal_mean_qos(reports):
	"""
	mobile-trace
	wire-trace
	stable-trace
	fluctuate-trace
	:param reports:
	:return:
	"""
	pass


def draw_cdf_fig(reports, compare_tag):
	"""
	比较不同算法在同一trace下的使用
	:return:
	"""
	# fig_save_path
	fig_save_path = "./result/cdf/" + compare_tag + "/" + reports[0].trace_name + "/"
	# deep-blue,green,red,yellow,purple
	colors = ["#2F7FC1", "#96C37D", "#D8383A", "#F3D266", "#C497B2"]
	shapes = ["-", "--", "-.", ":", "-"]
	
	# delay-cdf
	delay_fig_dict = {
		"x-label": "CDF",
		"y-label": "delay(ms)",
		"dir": fig_save_path,
		"file": "delay-cdf"
	}
	delay_fig = Figure(delay_fig_dict, [])
	for index, value in enumerate(reports):
		c_dict = {
			"name": value.algo,
			"color": colors[index],
			"shape": shapes[index]
		}
		c = CdfCurve(c_dict)
		c.update(value.delay)
		delay_fig.curves.append(c)
	delay_fig.save()
	
	# recv-cdf
	recv_fig_dict = {
		"x-label": "CDF",
		"y-label": "recv(kbps)",
		"dir": fig_save_path,
		"file": "recv-cdf"
	}
	recv_fig = Figure(recv_fig_dict, [])
	for index, value in enumerate(reports):
		c_dict = {
			"name": value.algo,
			"color": colors[index],
			"shape": shapes[index]
		}
		c = CdfCurve(c_dict)
		c.update(value.receiveRate)
		c.yAxisUnit("kbps")
		recv_fig.curves.append(c)
	recv_fig.save()
	
	# loss-cdf
	loss_fig_dict = {
		"x-label": "CDF",
		"y-label": "loss ratio(%)",
		"dir": fig_save_path,
		"file": "loss-cdf"
	}
	loss_fig = Figure(loss_fig_dict, [])
	for index, value in enumerate(reports):
		c_dict = {
			"name": value.algo,
			"color": colors[index],
			"shape": shapes[index]
		}
		c = CdfCurve(c_dict)
		c.update(value.loss)
		loss_fig.curves.append(c)
	loss_fig.save()
