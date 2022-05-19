import matplotlib.pyplot as plt
import os
import numpy as np
import math


class Curve:
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
	
	def update(self, data):
		self.x = [x for x in range(len(data))]  # original unit : interval(60ms)
		self.y = data


class Figure:
	def __init__(self, args: dict, curves):
		"""
		title:str
		x-label:
		y-label:
		dir:
		file:
		:param args:
		:return:
		"""
		self.attr = args
		self.curves = list(curves)
	
	def xAxisUnit(self, unit):
		if unit == "second":
			for index in range(len(self.curves)):
				self.curves[index].x = [tmp * 60 / 1000 for tmp in self.curves[index].x]
	
	def save(self):
		if not os.path.exists(self.attr["dir"]):
			os.makedirs(self.attr["dir"])
		for ele in self.curves:
			plt.plot(ele.x, ele.y, ele.attr["shape"], color=ele.attr["color"], label=ele.attr["name"])
		plt.xlabel(self.attr["x-label"])
		plt.ylabel(self.attr["y-label"])
		plt.legend()
		plt.savefig(self.attr["dir"] + self.attr["file"])
		plt.close()


class QosReport:
	def __init__(self):
		# ========================= common metric ======================== #
		self.fig_dir = None
		self.data_dir = None
		self.trace_name = None
		self.algo = None
		self.delay = []  # interval-ms
		self.loss = []  # interval-ratio
		self.targetRate = []  # interval:目标码率 bps
		self.receiveRate = []  # interval:实际接收码率 bps
		self.cap = []  # interval:link kbps
		
		# =========================gcc native 、 gemini gcc metric===================== #
		self.queueDelayDelta = []  # interval:
		self.gamma = []  # interval:
		self.aimd = []  # interval: -1(decrease),0(hold),1(near_max),2(max_unknown)
		self.queueDelayDelta_m = []  # 测量值(真实值）
		
		# ======================== drl metric #
		self.reward = []
		
		# ================ optimal metric
		self.object_U = 0.0
		
		# ================ qos metric
		self.util = 0.0
		self.d_aver = 0.0
		self.d_50 = 0.0
		self.d_95 = 0.0
		self.d_max = 0.0
		self.d_min = 0.0
		self.l_aver = 0.0
		
		self.cut_num = 0
		self.qos_u = 0.0
		self.qos_d = 0.0
		self.qos_l = 0.0
		self.qos = 0.0
	
	def init(self, algo_name, trace, isSaved=True):
		# algo_name should be str
		self.algo = algo_name
		self.trace_name = trace.name
		self.cap = [x.capacity for x in trace.tracePatterns]
		
		self.data_dir = "./result/" + self.algo + "/" + self.trace_name + "/data/"
		self.fig_dir = "./result/" + self.algo + "/" + self.trace_name + "/fig/"
		
		if not isSaved:
			return
		if not os.path.exists(self.fig_dir):
			os.makedirs(self.fig_dir)
		if not os.path.exists(self.data_dir):
			os.makedirs(self.data_dir)
	
	def update(self, recv_rate, d, l, lastBwe):
		self.delay.append(d)
		self.loss.append(l)
		self.targetRate.append(lastBwe)
		self.receiveRate.append(recv_rate)
	
	# def getDrlState(self):
	
	def draw_rate_fig(self):
		targetDict = {
			"name": self.algo,
			"color": "#FFBE7A",  # yellow
			"shape": "-"
		}
		target = Curve(targetDict)
		target.update([x / 1000 for x in self.targetRate])
		
		linkCapDict = {
			"name": "link capacity",
			"color": "#FA7F6F",  # red
			"shape": "-"
		}
		linkCap = Curve(linkCapDict)
		linkCap.update(self.cap)
		
		recvDict = {
			"name": "recv",
			"color": "#8ECFC9",  # green
			"shape": "--"
		}
		recv = Curve(recvDict)
		recv.update([x / 1000 for x in self.receiveRate])
		
		# ====================
		figDict = {
			# "title": "",
			"x-label": "time(second)",
			"y-label": "bandwidth(kbps)",
			"dir": self.fig_dir,
			"file": self.algo + "-" + self.trace_name + "-rate"
		}
		rate_fig = Figure(figDict, [target, linkCap, recv])
		rate_fig.xAxisUnit("second")
		rate_fig.save()
	
	def draw_delay_fig(self):
		"""
		delay
		:return:
		"""
		delayDict = {
			"name": "queue delay",
			"color": "#82B0D2",  # blue
			"shape": "-"
		}
		delay = Curve(delayDict)
		delay.update(self.delay)
		figDict = {
			# "title": "",
			"x-label": "time(second)",
			"y-label": "queue delay(ms)",
			"dir": self.fig_dir,
			"file": self.algo + "-" + self.trace_name + "-queueDelay"
		}
		delay_fig = Figure(figDict, [delay])
		delay_fig.xAxisUnit("second")
		delay_fig.save()
	
	def draw_loss_fig(self):
		"""
		loss
		:return:
		"""
		lossDict = {
			"name": "loss",
			"color": "#82B0D2",  # blue
			"shape": "-"
		}
		loss = Curve(lossDict)
		loss.update(self.loss)
		figDict = {
			# "title": "",
			"x-label": "time(second)",
			"y-label": "loss ratio",
			"dir": self.fig_dir,
			"file": self.algo + "-" + self.trace_name + "-lossRatio"
		}
		loss_fig = Figure(figDict, [loss])
		loss_fig.xAxisUnit("second")
		loss_fig.save()
	
	def draw_threshold_fig(self):
		"""
		
		:return:
		"""
		gamma_dict_1 = {
			"name": "threshold positive",
			"color": "#FA7F6F",  # red
			"shape": "-"
		}
		gamma_dict_2 = {
			"name": "threshold negative",
			"color": "#FA7F6F",  # red
			"shape": "-"
		}
		gamma_positive, gamma_negative = Curve(gamma_dict_1), Curve(gamma_dict_2)
		gamma_positive.update(self.gamma)
		gamma_negative.update([x * (-1) for x in self.gamma])
		
		queue_delay_gradient_dict = {
			"name": "queue delay gradient",
			"color": "#82B0D2",  # blue
			"shape": "-"
		}
		queue_delay_gradient = Curve(queue_delay_gradient_dict)
		queue_delay_gradient.update(self.queueDelayDelta)
		
		# =========================
		fig_dict = {
			"x-label": "time(second)",
			"y-label": "",
			"dir": self.fig_dir,
			"file": self.algo + "-" + self.trace_name + "-threshold"
		}
		fig = Figure(fig_dict, [gamma_positive, gamma_negative, queue_delay_gradient])
		fig.xAxisUnit("second")
		fig.save()
	
	def draw_reward_fig(self):
		pass
	
	def calculateU(self):
		# u
		# print("util: %s", self.util)
		# print("delay: %s", self.d_aver / 1000.0)
		self.object_U = math.log(np.mean(self.receiveRate) / 1000.0) - (3.0 / 7.0) * math.log(np.mean(self.delay))
	
	def printResult(self):
		"""
		algo_name
		util
		average_delay
		50th_delay
		95th_delay
		loss
		qos_u
		qos_d
		qos_l
		qos
		"""
		res_list = [self.util, self.d_aver, self.d_50, self.d_95, self.l_aver, self.qos_u, self.qos_d, self.qos_l,
		            self.qos]
		# print(res_list)
		res_list = [str(x) for x in res_list]
		with open(self.data_dir + "qos_result", "w") as f:
			res = self.algo + " & " + " & ".join(res_list) + " \\\\ "
			f.write(res)
		return res_list
	
	def calculateQos(self):
		self.d_aver = round(np.mean(self.delay), 2)
		self.d_50 = round(np.median(self.delay), 2)
		self.d_95 = round(np.percentile(self.delay, 95), 2)
		self.d_max = round(np.max(self.delay), 2)
		self.d_min = round(np.min(self.delay), 2)
		self.l_aver = round(np.mean(self.loss), 2)
		
		self.util = round(self.utilsCal(), 2)
		
		self.qos_u = round(100 * self.util, 2)
		
		if self.d_max - self.d_min == 0:
			self.qos_d = 100
		else:
			self.qos_d = round(100 * (self.d_max - self.d_95) / (self.d_max - self.d_min), 2)
		
		self.qos_l = round(100 * (1 - self.l_aver), 2)
		
		self.qos = round(0.35 * self.qos_u + 0.15 * self.qos_d + 0.5 * self.qos_l, 2)
	
	def utilsCal(self):
		utils = []
		recv_rate_kbps = [x / 1000 for x in self.receiveRate]
		length = min(len(recv_rate_kbps), len(self.cap))
		for index in range(length):
			if recv_rate_kbps[index] >= self.cap[index]:
				utils.append(1)
			else:
				utils.append(float(recv_rate_kbps[index]) / float(self.cap[index]))
		return np.mean(utils)
	
	def draw_special_01(self):
		"""
		绘制两种时延梯度估计方案的估计结果，并与真实时延变化量比较
		:return:
		"""
		pass
