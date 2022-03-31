import glob
import json
import os.path
from typing import List

import matplotlib.pyplot as plt
import numpy as np

figSavePath = "traceFig/"


class TracePattern(object):
	def __init__(self):
		self.duration = 0.0
		self.capacity = 0.0
		self.loss = 0.0
		self.jitter = 0.0
		self.rtt = 0.0
		self.time = 0.0


def preprocess(path):
	name, data = getTrace(path)
	
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


def dict2TracePattern(data):
	tmp = TracePattern()
	for index in ["duration", "capacity", "loss", "jitter", "rtt"]:
		v = data.get(index, 0.0)
		setattr(tmp, index, v)
	return tmp


def drawCurve(data: List[TracePattern], attr, name, path):
	x = []
	y = []
	tempTime = 0
	for ts in data:
		x.append(tempTime)
		y.append(getattr(ts, attr))
		tempTime += ts.duration
	
	# 进行简单的滤波，去除异常点
	#
	yM = abs(np.median(y))
	for i, v in enumerate(y):
		if abs(v) > 10 * yM:
			y[i] = y[i - 1]
	
	plt.plot(x, y, label=name)
	plt.xlabel("t/ms")
	if attr == "capacity":
		plt.ylabel("cap/kbps")
	plt.title(name + " " + attr + "-curve")
	plt.legend()
	plt.savefig(path + name + " " + attr + "-curve")
	plt.close()


def getTrace(path) -> (str, List[TracePattern]):
	fileName = os.path.basename(path).split(".")[0]
	ts = []
	with open(path, "r") as f:
		data = json.load(f)
		for ele in data["uplink"]["trace_pattern"]:
			t = dict2TracePattern(ele)
			ts.append(t)
	return fileName, ts


# def drawCurveWithInterval()

def traceWithCapacity():
	# traceDir = os.path.join(os.path.dirname(__file__), "../traces")
	traceFiles = glob.glob(f"../traces/*.json")
	if not os.path.exists(figSavePath):
		os.makedirs(figSavePath)
	
	for path in traceFiles:
		name, data = getTrace(path)
		drawCurve(data, "capacity", name, figSavePath)
	# break


# drawCurve(ts, "rtt", fileName, figSavePath)


if __name__ == "__main__":
	traceWithCapacity()
