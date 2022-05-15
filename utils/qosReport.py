import matplotlib.pyplot as plt


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
		self.curves = curves
	
	def xAxisUnit(self, unit):
		if unit == "second":
			for index in range(len(self.curves)):
				self.curves[index] = [tmp * 60 / 1000 for tmp in self.curves[index]]
	
	def save(self):
		for ele in self.curves:
			plt.plot(ele.x, ele.y, ele.attr["shape"], color=ele.attr["color"], label=ele.attr.name)
		plt.xlabel(self.attr["x-label"])
		plt.ylabel(self.attr["y-label"])
		plt.legend()
		plt.savefig(self.attr["dir"] + "/" + self.attr["file"])
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
		self.trend = []  # interval: -1(decrease),0(hold),1(near_max),2(max_unknown)
		
		# ======================== drl metric #
		self.reward = []
	
	def init(self, algo_name, trace):
		self.algo = algo_name
		self.trace_name = trace.name
		self.cap = [x.capacity for x in trace.tracePatterns]
		
		self.data_dir = "result/" + self.algo + "/" + self.trace_name + "/data"
		self.fig_dir = "result/" + self.algo + "/" + self.trace_name + "/fig"
	
	def update(self, recv_rate, d, l, lastBwe):
		self.delay.append(d)
		self.loss.append(l)
		self.targetRate.append(lastBwe)
		self.receiveRate.append(recv_rate)
	
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
		gamma_dict = {
			"name": "threshold",
			"color": "#FA7F6F",  # red
			"shape": "-"
		}
		gamma_positive, gamma_negative = Curve(gamma_dict), Curve(gamma_dict)
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
