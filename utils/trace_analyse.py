import glob
import json
import os.path
from typing import List

import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import savgol_filter

from plot.plotTool import Line


class TracePattern(object):
	def __init__(self):
		self.duration = 0.0
		self.capacity = 0.0
		self.loss = 0.0
		self.jitter = 0.0
		self.rtt = 0.0
		self.time = 0.0


def dict2TracePattern(data):
	tmp = TracePattern()
	for index in ["duration", "capacity", "loss", "jitter", "rtt"]:
		v = data.get(index, 0.0)
		if index == "capacity":  # turn unit to mbps
			v = v / 1000
		setattr(tmp, index, v)
	return tmp


def preprocess(data: List[TracePattern]) -> List[TracePattern]:
	tmpTime = 0.0
	attrM = abs(np.median([x.capacity for x in data]))
	last = None
	
	result = []
	for ts in data:
		ts.time = tmpTime
		tmpTime += ts.duration
		if abs(ts.capacity) > 10 * attrM:
			ts.capacity = last
		last = ts.capacity
		result.append(ts)
	return result


def readTrace(path) -> (str, List[TracePattern]):
	fileName = os.path.basename(path).split(".")[0]
	ts = []
	with open(path, "r") as f:
		data = json.load(f)
		for ele in data["uplink"]["trace_pattern"]:
			t = dict2TracePattern(ele)
			ts.append(t)
	return fileName, ts


def drawCurve(data: List[TracePattern], attr, name, path):
	x = []
	y = []
	tempTime = 0
	for ts in data:
		x.append(tempTime)
		y.append(getattr(ts, attr))
		tempTime += ts.duration
	
	# 进行简单的滤波，去除异常点
	yM = abs(np.median(y))
	for i, v in enumerate(y):
		if abs(v) > 10 * yM:
			y[i] = y[i - 1]
	
	x = [int(tmp / 60) for tmp in x]
	y = savgol_filter(y, 21, 1, mode="nearest")
	plt.plot(x, y, label=name)
	plt.xlabel("t/interval")
	if attr == "capacity":
		plt.ylabel("cap/mbps")
	plt.title(name + " " + attr + "-curve")
	plt.legend()
	plt.savefig(path + name + " " + attr + "-curve")
	plt.close()


def drawCurveV2(data: List[TracePattern], attr, name):
	x = []
	y = []
	tempTime = 0
	for ts in data:
		x.append(tempTime)
		y.append(getattr(ts, attr))
		tempTime += ts.duration
	
	# 进行简单的滤波，去除异常点
	yM = abs(np.median(y))
	for i, v in enumerate(y):
		if abs(v) > 10 * yM:
			y[i] = y[i - 1]
	
	x = [int(tmp / 60) for tmp in x]
	y = savgol_filter(y, 21, 1, mode="nearest")
	
	tmp = Line()
	tmp.x = x
	tmp.y = y
	tmp.name = name
	return tmp


def genTraceCap(path) -> Line:
	name, tmpp = readTrace(path)
	data = preprocess(tmpp)
	return drawCurveV2(data, "capacity", name)


if __name__ == "__main__":
	figSavePath = "traceFig/"
	traceFiles = glob.glob(f"../mytraces/*.json")
	for ele in traceFiles:
		name, tmpp = readTrace(ele)
		data = preprocess(tmpp)
		drawCurve(data, "capacity", name, figSavePath)
# print(data)
