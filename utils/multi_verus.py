import matplotlib.pyplot as plt
import numpy as np
from utils.my_enum import traceSetType
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


def read_qos_file(file):
	with open(file, "r") as f:
		qos_ = f.readline()
		qos = [x.strip() for x in qos_.split("&")]
		qos = qos[1:]
		qos[-1] = qos[-1].replace("\\\\", "")
		res = [float(x) for x in qos]
		print(res)
		return res


def cal_mean_qos(algo_names, net_type):
	"""
	
	mobile-trace
	wire-trace
	
	# stable-trace
	# fluctuate-trace
	
	real-world-trace
	:param reports:
	:return:
	"""
	mobile_trace = ["4G_500kbps", "4G_700kbps", "4G_3mbps", "WIRED_200kbps", "WIRED_900kbps"]
	# "5G_12mbps", "5G_13mbps",
	# "WIRED_35mbps"
	wired_trace = ["WIRED_200kbps", "WIRED_900kbps"]
	
	if net_type == traceSetType.WIRED:
		for ele in algo_names:
			print("=" * 4)
			print(ele.value)
			sum_list = []
			save_file = "./result/" + ele.value + "/" + net_type.value + "/mean_"
			for t in wired_trace:
				data_file = "./result/" + ele.value + "/" + t + "/data/qos_result"
				sum_list = np.sum([sum_list, read_qos_file(data_file)], axis=0)
			mean_list = [round(x / len(wired_trace), 2) for x in sum_list]
			
			res_list = [str(x) for x in mean_list]
			res = ele.value + " & " + " & ".join(res_list) + " \\\\ "
			print(res)
			print("=" * 4)
	
	if net_type == traceSetType.LTE:
		for ele in algo_names:
			print("=" * 4)
			print(ele.value)
			sum_list = []
			save_file = "./result/" + ele.value + "/" + net_type.value + "/mean_"
			for t in mobile_trace:
				data_file = "./result/" + ele.value + "/" + t + "/data/qos_result"
				sum_list = np.sum([sum_list, read_qos_file(data_file)], axis=0)
			mean_list = [round(x / len(mobile_trace), 2) for x in sum_list]
			res_list = [str(x) for x in mean_list]
			res = ele.value + " & " + " & ".join(res_list) + " \\\\ "
			print(res)
			print("=" * 4)


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
