import json
import os
import random

from utils.plotTool import Line, drawLineV2
import numpy as np
import matplotlib.pyplot as plt

ATTR = ["recvRate", "gccRate", "delay", "loss", "cap", "hatRate", "esimate", "bound_up"]


class Algo:
	def __init__(self, algoName, path):
		self.algoName = algoName
		self.path = path
		self.traceResult = {}
	
	def run(self):
		for _, _, files in os.walk(self.path):
			for file in files:
				file_info = file.split("-")
				trace_name = file_info[0]
				axis = file_info[-1]
				if len(file_info) == 2:
					# is capacity attr
					result_attr = "cap"
				else:
					result_attr = file_info[1]
				if result_attr not in ATTR:
					continue
				with open(self.path + "/" + file) as f:
					data = json.loads(f.read())
				self.updateTraceResult(trace_name, result_attr, axis, data)
		
		for v in self.traceResult.values():
			# v.cut()
			v.calculate()
	
	def updateTraceResult(self, trace_name, attr, axis, data):
		if trace_name not in self.traceResult:
			self.traceResult[trace_name] = traceResult(trace_name)
		self.traceResult[trace_name].add(attr, axis, data)
	
	def returnTraceResult(self, trace_name):
		return self.traceResult[trace_name].returnResult()


class traceResult:
	def __init__(self, trace_name):
		self.traceName = trace_name
		self.traceCapLine = Line()
		self.traceCapLine.name = "link capacity"  # kbps
		self.traceCapLine.y_label = "rate(kbps)"
		self.delayLine = Line()
		self.delayLine.name = "queue delay"  # ms
		self.delayLine.y_label = "queue delay(ms)"
		self.lossLine = Line()
		self.lossLine.name = "loss"
		self.lossLine.y_label = "loss ratio"
		self.sendingRate = Line()
		self.sendingRate.name = "recv rate"  # kbps
		self.targetRate = Line()
		self.targetRate.name = "estimate bandwidth"  # kbps
		
		self.threshold = Line()
		self.threshold.name = "threshold(gamma)"
		self.threshold.y_label = ""
		self.estimateD = Line()
		self.estimateD.name = "queue delay gradient"
		
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
	
	def add(self, attr, axis, data):
		if attr == "recvRate":
			if axis == "xaxis":
				self.sendingRate.x = data
			if axis == "yaxis":
				self.sendingRate.y = data
		if attr == "gccRate":
			if axis == "xaxis":
				self.targetRate.x = data
			if axis == "yaxis":
				self.targetRate.y = data
		if attr == "delay":
			if axis == "xaxis":
				self.delayLine.x = data
			if axis == "yaxis":
				self.delayLine.y = data
		if attr == "loss":
			if axis == "xaxis":
				self.lossLine.x = data
			if axis == "yaxis":
				self.lossLine.y = data
		if attr == "cap":
			if axis == "xaxis":
				self.traceCapLine.x = data
			if axis == "yaxis":
				self.traceCapLine.y = data
		if attr == "threshold":
			if axis == "xaxis":
				self.threshold.x = data
			if axis == "yaxis":
				self.threshold.y = data
		if attr == "esimate":
			if axis == "xaxis":
				self.estimateD.x = data
			if axis == "yaxis":
				self.estimateD.y = data
	
	def cut(self):
		for ele in self.sendingRate.y:
			if ele <= 0:
				self.cut_num += 1
		self.traceCapLine.y = self.traceCapLine.y[self.cut_num:-1]
		self.delayLine.y = self.delayLine.y[self.cut_num:-1]
		self.lossLine.y = self.lossLine.y[self.cut_num:-1]
		self.sendingRate.y = self.sendingRate.y[self.cut_num:-1]
		self.targetRate.y = self.targetRate.y[self.cut_num:-1]
	
	def utilsCal(self):
		utils = []
		length = min(len(self.sendingRate.y), len(self.traceCapLine.y))
		for index in range(length):
			if self.sendingRate.y[index] >= self.traceCapLine.y[index]:
				utils.append(1)
			else:
				utils.append(float(self.sendingRate.y[index]) / float(self.traceCapLine.y[index]))
		# print(self.traceName)
		return np.mean(utils)
	
	def calculate(self):
		self.d_aver = round(np.mean(self.delayLine.y), 2)
		self.d_50 = round(np.median(self.delayLine.y), 2)
		self.d_95 = round(np.percentile(self.delayLine.y, 95), 2)
		self.d_max = round(np.max(self.delayLine.y), 2)
		self.d_min = round(np.min(self.delayLine.y), 2)
		self.l_aver = round(np.mean(self.lossLine.y), 2)
		
		self.util = round(self.utilsCal(), 2)
		
		# if self.util > 1:
		# 	z = self.util - 1
		# 	self.util = 1 - z - random.random() * (0.2 - z)
		# if self.util == 1:
		# 	self.util = 1 - random.random() * 0.15
		
		self.qos_u = round(100 * self.util, 2)
		
		if self.d_max - self.d_min == 0:
			self.qos_d = 100
		else:
			self.qos_d = round(100 * (self.d_max - self.d_95) / (self.d_max - self.d_min), 2)
		
		self.qos_l = round(100 * (1 - self.l_aver), 2)
		
		self.qos = round(0.35 * self.qos_u + 0.15 * self.qos_d + 0.5 * self.qos_l, 2)
	
	def returnResult(self):
		return (
			f"{round(self.util, 2)} & "
			f"{round(self.d_aver, 2)} & "
			f"{round(self.d_50, 2)} & "
			f"{round(self.d_95, 2)} & "
			f"{round(self.l_aver, 2)} & "
			f"{round(self.qos_u, 2)} & "
			f"{round(self.qos_d, 2)} & "
			f"{round(self.qos_l, 2)} & "
			f"{round(self.qos, 2)} & "
		)


def printResult():
	RTS_DRL_DIR = "/Users/hansenma/mhspion/rtcplayground/result/result-drl"
	GCC_DIR = "/Users/hansenma/mhspion/rtcplayground/result/result-GeminiGCC"
	RTS_RULE_DIR = "/Users/hansenma/mhspion/rtcplayground/result/result-GCC-Native"
	RTS_HYBIRD = "/Users/hansenma/mhspion/rtcplayground/result/result-GCC-RTS"
	RTS_DRL_PRO_DIR = "/Users/hansenma/mhspion/rtcplayground/result/result-drl-enhance"
	RTS_HYBIRD_PRO = "/Users/hansenma/mhspion/rtcplayground/result/result-GCC-RTS-enhance"
	
	gcc = Algo("GCC", GCC_DIR)
	rule = Algo("RTS-RULE", RTS_RULE_DIR)
	drl = Algo("RTS-DRL", RTS_DRL_DIR)
	hybird = Algo("RTS-HYBIRD", RTS_HYBIRD)
	drl_pro = Algo("RTS-DRL-PRO", RTS_DRL_PRO_DIR)
	hybird_pro = Algo("RTS-HYBIRD-PRO", RTS_HYBIRD_PRO)
	gcc.run()
	rule.run()
	drl.run()
	hybird.run()
	drl_pro.run()
	hybird_pro.run()
	target = [gcc, rule, drl, hybird, drl_pro, hybird_pro]
	with open("final-result", "w") as f:
		res = ""
		for key in gcc.traceResult:
			res += key + "\n"
			for ele in target:
				res += ele.algoName + " "
				res += ele.returnTraceResult(key)
				res += "\n"
			res += "\n\n"
		f.write(res)


# netType = [["4G", "5G"], ["WIRED"]]
# for type in netType:
# 	for algo in target:
# 		res = "\n"
# 		res += algo.algoName + " "
# 		util = []
# 		d_avr = []
# 		d_50 = []
# 		d_95 = []
# 		l = []
# 		qu = []
# 		qd = []
# 		ql = []
# 		q = []
# 		for key in algo.traceResult:
# 			if key[0:5] not in type:
# 				continue
# 			tmp = algo.traceResult[key]
# 			util.append(tmp.util)
# 			d_avr.append(tmp.d_aver)
# 			d_50.append(tmp.d_50)
# 			d_95.append(tmp.d_95)
# 			l.append(tmp.l_aver)
# 			qu.append(tmp.qos_u)
# 			qd.append(tmp.qos_d)
# 			ql.append(tmp.qos_l)
# 			q.append(tmp.qos)
# 		if len(util) == 0:
# 			continue
# 		res += str(np.mean(util)) + " util "
# 		res += str(np.mean(d_avr)) + " d_avr "
# 		res += str(np.mean(d_50)) + " d_50 "
# 		res += str(np.mean(d_95)) + " d_95 "
# 		res += str(np.mean(l)) + " l "
# 		res += str(np.mean(qu)) + " qu "
# 		res += str(np.mean(qd)) + " qd "
# 		res += str(np.mean(ql)) + " ql "
# 		res += str(np.mean(q)) + " q "
# 		print(res)


def draw():
	RTS_DRL_DIR = "/Users/hansenma/mhspion/rtcplayground/result/result-drl"
	GCC_DIR = "/Users/hansenma/mhspion/rtcplayground/result/result-GeminiGCC"
	RTS_RULE_DIR = "/Users/hansenma/mhspion/rtcplayground/result/result-GCC-Native"
	RTS_HYBIRD = "/Users/hansenma/mhspion/rtcplayground/result/result-GCC-RTS"
	RTS_DRL_PRO_DIR = "/Users/hansenma/mhspion/rtcplayground/result/result-drl-enhance"
	RTS_HYBIRD_PRO = "/Users/hansenma/mhspion/rtcplayground/result/result-GCC-RTS-enhance"
	
	SPECIAL_DIR = "/Users/hansenma/mhspion/rtcplayground/result/special"
	SPECIAL2_DIR = "/Users/hansenma/mhspion/rtcplayground/result/special-only-delay"
	gcc = Algo("GCC", GCC_DIR)
	
	#
	rule = Algo("RTS-RULE", RTS_RULE_DIR)
	drl = Algo("RTS-DRL", RTS_DRL_DIR)
	hybird = Algo("RTS-HYBIRD", RTS_HYBIRD)
	drl_pro = Algo("RTS-DRL-PRO", RTS_DRL_PRO_DIR)
	hybird_pro = Algo("RTS-HYBIRD-PRO", RTS_HYBIRD_PRO)
	#
	drl_pro.run()
	hybird_pro.run()
	gcc.run()
	rule.run()
	drl.run()
	hybird.run()
	
	# target = [gcc, rule, drl, hybird]
	
	dir = "final-picture"
	
	trace_name_1 = ["4G_500kbps", "WIRED_200kbps", "4G_700kbps", "WIRED_900kbs", "4G_3mbps"]
	trace_name_2 = ["special01", "special02", "04", "03"]
	
	# for ele in trace_name_1:
	# 	cap = gcc.traceResult[ele].traceCapLine
	# 	sending = gcc.traceResult[ele].sendingRate
	# 	target = gcc.traceResult[ele].targetRate
	# 	d = gcc.traceResult[ele].delayLine
	# 	l = gcc.traceResult[ele].lossLine
	# 	drawLineV2(dir, ele + "_gcc_rate", cap, sending, target)
	# 	drawLineV2(dir, ele + "_gcc_delay", d)
	# 	drawLineV2(dir, ele + "_gcc_loss", l)
	
	alogs = [gcc, rule, drl, hybird, drl_pro, hybird_pro]
	for ele in trace_name_1:
		if ele != trace_name_1[2]:
			continue
		tmpAlog = alogs[1]
		cap = tmpAlog.traceResult[ele].traceCapLine
		sending = tmpAlog.traceResult[ele].sendingRate
		target = tmpAlog.traceResult[ele].targetRate
		d = tmpAlog.traceResult[ele].delayLine
		l = tmpAlog.traceResult[ele].lossLine
		gamma = tmpAlog.traceResult[ele].threshold
		qd = tmpAlog.traceResult[ele].estimateD
		drawLineV2(dir, ele + "_rule_rate", gamma, qd, smooth=False)


# drawLineV2(dir, ele + "_rule_rate", cap, sending, target, smooth=True)


# drawLinev3()


def drawLinev3():
	gammay = []
	gammax = []
	# gammaFile = "/Users/hansenma/mhspion/rtcplayground/result/special/special02-threshold-GCC-Native-yaxis"
	gammaFile = "/Users/hansenma/mhspion/rtcplayground/result/result-GCC-Native/WIRED_200kbps-threshold-GCC-Native-yaxis"
	# gammaFile2 = "/Users/hansenma/mhspion/rtcplayground/result/special/special02-threshold-GCC-Native-xaxis"
	gammaFile2 = "/Users/hansenma/mhspion/rtcplayground/result/result-GCC-Native/WIRED_200kbps-threshold-GCC-Native-xaxis"
	queuey = []
	queuex = []
	# queueFile = "/Users/hansenma/mhspion/rtcplayground/result/special-only-delay/special02-esimate-GCC-Native-yaxis"
	queueFile = "/Users/hansenma/mhspion/rtcplayground/result/result-GCC-Native/WIRED_200kbps-esimate-GCC-Native-yaxis"
	# queuexFile = "/Users/hansenma/mhspion/rtcplayground/result/special-only-delay/special02-esimate-GCC-Native-xaxis"
	queuexFile = "/Users/hansenma/mhspion/rtcplayground/result/result-GCC-Native/WIRED_200kbps-esimate-GCC-Native-xaxis"
	with open(queuexFile, 'r') as f:
		queuex = json.loads(f.read())
	with open(gammaFile, "r") as f:
		gammay = json.loads(f.read())
	with open(queueFile, "r") as f:
		queuey = json.loads(f.read())
	with open(gammaFile2, "r") as f:
		gammax = json.loads(f.read())
	queuex = [tmp * 60 / 1000 for tmp in queuex]
	gammax = [tmp * 60 / 1000 for tmp in gammax]
	y2 = [-1 * tmp for tmp in gammay]
	
	plt.plot(queuex, queuey, '-', color='#82B0D2', label="queue delay gradient")
	
	plt.plot(gammax, gammay, '--', color='#FA7F6F', label="threshold(gamma)")
	plt.plot(gammax, y2, '--', color='#FA7F6F')
	plt.xlabel("time(second)")
	plt.legend()
	plt.savefig("test")
	plt.close()


def drawLinev4():
	gammay = []
	gammax = []
	# gammaFile = "/Users/hansenma/mhspion/rtcplayground/result/special/special02-threshold-GCC-Native-yaxis"
	gammaFile = "/Users/hansenma/mhspion/rtcplayground/result/result-GCC-Native/WIRED_200kbps-threshold-GCC-Native-yaxis"
	# gammaFile2 = "/Users/hansenma/mhspion/rtcplayground/result/special/special02-threshold-GCC-Native-xaxis"
	gammaFile2 = "/Users/hansenma/mhspion/rtcplayground/result/result-GCC-Native/WIRED_200kbps-threshold-GCC-Native-xaxis"
	queuey = []
	queuex = []
	# queueFile = "/Users/hansenma/mhspion/rtcplayground/result/special-only-delay/special02-esimate-GCC-Native-yaxis"
	queueFile = "/Users/hansenma/mhspion/rtcplayground/result/result-GCC-Native/WIRED_200kbps-esimate-GCC-Native-yaxis"
	# queuexFile = "/Users/hansenma/mhspion/rtcplayground/result/special-only-delay/special02-esimate-GCC-Native-xaxis"
	queuexFile = "/Users/hansenma/mhspion/rtcplayground/result/result-GCC-Native/WIRED_200kbps-esimate-GCC-Native-xaxis"
	with open(queuexFile, 'r') as f:
		queuex = json.loads(f.read())
	with open(gammaFile, "r") as f:
		gammay = json.loads(f.read())
	with open(queueFile, "r") as f:
		queuey = json.loads(f.read())
	with open(gammaFile2, "r") as f:
		gammax = json.loads(f.read())
	queuex = [tmp * 60 / 1000 for tmp in queuex]
	gammax = [tmp * 60 / 1000 for tmp in gammax]
	y2 = [-1 * tmp for tmp in gammay]
	
	plt.plot(queuex, queuey, '-', color='#82B0D2', label="queue delay gradient")
	
	plt.plot(gammax, gammay, '--', color='#FA7F6F', label="threshold(gamma)")
	plt.plot(gammax, y2, '--', color='#FA7F6F')
	plt.xlabel("time(second)")
	plt.legend()
	plt.savefig("test")
	plt.close()


# drawLineV2(dir, ele + "_rule_delay", d)
# drawLineV2(dir, ele + "_rule_loss", l)


if __name__ == "__main__":
	printResult()
# draw()
# drawLinev3()
