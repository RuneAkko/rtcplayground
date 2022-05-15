import copy
import json
import os

import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import savgol_filter

from utils.plotTool import Line


class TraceFig(object):
	
	def __init__(self):
		self.title = None
		self.xLabel = None
		self.yLabel = None
		self.x = []
		self.y = []
		self.yLineLabel = None
		self.figSavePath = None


class TracePattern(object):
	def __init__(self):
		"""
		"trace_pattern": [
                            {
                                "duration": 60000, # duration time (ms)
                                "capacity": 300,   # link bandwidth (kbps)
                                "loss": 0.1,       # loss rate (0.0~0.1)
                                "rtt" : 85,        # round trip delay (ms)
                                "jitter": 0,       # not supported in current version
                            },
		"""
		self.duration = 0.0  # ms
		self.capacity = 0.0  # kbps
		self.loss = 0.0
		self.jitter = 0.0
		self.rtt = 0.0
		self.time = 0.0  # ms,  abs time


class Trace(object):
	def __init__(self, path=None):
		self.tracePatterns = []
		self.newTracePatterns = None
		self.name = None
		self.path = path
		self.traceFig = None
	
	def readTraceFile(self):
		self.name = os.path.basename(self.path).split(".")[0]
		
		with open(self.path, "r") as f:
			jsonData = json.load(f)
			for ele in jsonData["uplink"]["trace_pattern"]:
				t = _dict2ts(ele)
				self.tracePatterns.append(t)
	
	def writeTraceFile(self, new_path):
		if self.newTracePatterns is None:
			self.newTracePatterns = self.tracePatterns
		
		template = {
			"type": "video",
			"downlink": {},
			"uplink": {
				"trace_pattern": []
			}
		}
		for ele in self.newTracePatterns:
			tmp = {}
			for index in ["duration", "capacity", "loss", "jitter", "time"]:
				if index == "capacity":
					tmp[index] = max(getattr(ele, index), 50)  # capacity > 0
				else:
					tmp[index] = getattr(ele, index)
			template["uplink"]["trace_pattern"].append(tmp)
		json_str = json.dumps(template, indent=1)
		with open(new_path + self.name + ".json", "w") as f:
			f.write(json_str)
	
	def processOri(self):
		self.preFilter()
		self.filterForTime()
	
	def preFilter(self):
		"""
		1. 原始 trace 的滤波。主要过滤极端值：替换法。 cap<=中位数10倍。
		2. cap 极小的值也替换掉 < 50kbps，替换为50kbps。
		2. 持续时间戳 -> 绝对时间戳
		"""
		tmpTime = 0.0
		attrM = np.median([x.capacity for x in self.tracePatterns])
		for i, v in enumerate(self.tracePatterns):
			self.tracePatterns[i].time = tmpTime
			tmpTime += v.duration
			if v.capacity > 10 * attrM:
				self.tracePatterns[i].capacity = 10 * attrM
			if v.capacity < 50:
				self.tracePatterns[i].capacity = 50
	
	def filterForTime(self):
		"""
		原有 trace 时间不均匀，
		按 60ms 的时间粒度，转换为时间均匀的 trace pattern
		"""
		newTp = []
		tmpTime = 0
		for ele in self.tracePatterns:
			num = max(int(ele.duration / 60), 1)
			for e in range(num):
				tmp = copy.deepcopy(ele)
				tmp.duration = 60
				tmp.time = tmpTime
				tmpTime += 60
				newTp.append(tmp)
		self.tracePatterns = newTp

# # ======================= fig ============================ #
# def genLine(self, attr, smooth=False, interval=60) -> Line:
# 	x, y = [], []
# 	for ts in self.tracePatterns:
# 		x.append(ts.time / interval)
# 		y.append(getattr(ts, attr))
#
# 	# 平滑曲线，观察规律
# 	if smooth:
# 		y = savgol_filter(y, 11, 4, mode="nearest")
#
# 	tmp = Line()
# 	tmp.x = x
# 	tmp.y = y
# 	tmp.name = self.name
# 	tmp.attrName = attr
# 	return tmp
#
# def draw(self, fig: TraceFig):
# 	plt.plot(fig.x, fig.y, label=fig.yLineLabel)
# 	plt.xlabel(fig.xLabel)
# 	plt.ylabel(fig.yLabel)
# 	plt.title(fig.title)
#
# 	plt.legend()
# 	plt.savefig(fig.figSavePath + fig.title)
# 	plt.close()
#
# def genFig(self, figSavePath="", line: Line = None):
# 	tmp = TraceFig()
# 	tmp.title = self.name + "  " + line.attrName + "-curve"
# 	tmp.xLabel = "time/ms"
# 	if line.attrName == "capacity":
# 		tmp.yLabel = "cap/kbps"
# 	tmp.x = line.x
# 	tmp.y = line.y
# 	tmp.yLineLabel = self.name
# 	tmp.figSavePath = figSavePath
# 	return tmp


"""
tool function
"""


# json 文件 -> trace pattern object
def _dict2ts(_data: dict) -> TracePattern:
	tmp = TracePattern()
	for index in ["duration", "capacity", "loss", "jitter", "time", "rtt"]:
		v = _data.get(index, 0.0)
		setattr(tmp, index, v)
	return tmp
