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
		self.duration = 0.0  # ms
		self.capacity = 0.0  # mbps
		self.loss = 0.0
		self.jitter = 0.0
		self.rtt = 0.0
		self.time = 0.0  # interval , 60ms


def _dict2ts(_data: dict) -> TracePattern:
	tmp = TracePattern()
	accTime = 0
	for index in ["duration", "capacity", "loss", "jitter", "rtt", "time"]:
		v = _data.get(index, 0.0)
		if index == "capacity":
			v = v / 1000.0  # turn kbps unit to mbps
		setattr(tmp, index, v)
	return tmp


class Trace(object):
	def __init__(self, traceFilePath=None):
		self.tracePatterns = []
		self.newTracePatterns = None
		self.traceName = None
		self.traceFilePath = traceFilePath
		
		self.traceFig = None
	
	def smooth(self, l):
		return savgol_filter(l, 11, 4, mode="nearest")
	
	def readTraceFile(self):
		traceName = os.path.basename(self.traceFilePath).split(".")[0]
		self.traceName = traceName
		
		with open(self.traceFilePath, "r") as f:
			jsonData = json.load(f)
			for ele in jsonData["uplink"]["trace_pattern"]:
				t = _dict2ts(ele)
				self.tracePatterns.append(t)
	
	def writeTraceFile(self, newTraceFilePath):
		if self.newTracePatterns is None:
			self.newTracePatterns = self.tracePatterns
		template = {
			"uplink": {
				"trace_pattern": []
			}
		}
		for ele in self.newTracePatterns:
			tmp = {}
			for index in ["duration", "capacity", "loss", "jitter", "rtt", "time"]:
				if index == "capacity":
					tmp[index] = getattr(ele, index) * 1000.0  # mbps to kbps
				else:
					tmp[index] = getattr(ele, index)
			template["uplink"]["trace_pattern"].append(tmp)
		json_str = json.dumps(template, indent=1)
		with open(newTraceFilePath + self.traceName + ".json", "w") as f:
			f.write(json_str)
	
	def preFilter(self):
		"""
		1. 原始 trace 的滤波。主要过滤极端值：替换法。 cap
		2. 持续时间戳 -> 绝对时间戳
		"""
		tmpTime = 0.0
		attrM = np.median([x.capacity for x in self.tracePatterns])
		last = None
		for i, v in enumerate(self.tracePatterns):
			self.tracePatterns[i].time = tmpTime
			tmpTime += v.duration
			if v.capacity > 10 * attrM:
				self.tracePatterns[i].capacity = last
			last = self.tracePatterns[i].capacity
	
	def genLine(self, attr, smooth=False) -> Line:
		x, y = [], []
		for ts in self.tracePatterns:
			x.append(ts.time)
			y.append(getattr(ts, attr))
		
		# trace time unit : ms -> interval step (60ms)
		x = [int(tmp / 60) for tmp in x]
		
		# 平滑曲线，观察规律
		if smooth:
			y = savgol_filter(y, 11, 4, mode="nearest")
		
		tmp = Line()
		tmp.x = x
		tmp.y = y
		tmp.name = self.traceName
		tmp.attrName = attr
		return tmp
	
	def draw(self, fig: TraceFig):
		plt.plot(fig.x, fig.y, label=fig.yLineLabel)
		plt.xlabel(fig.xLabel)
		plt.ylabel(fig.yLabel)
		plt.title(fig.title)
		
		plt.legend()
		plt.savefig(fig.figSavePath + fig.title)
		plt.close()
	
	def genFig(self, figSavePath="", line: Line = None):
		tmp = TraceFig()
		tmp.title = self.traceName + "  " + line.attrName + "-curve"
		tmp.xLabel = "time/interval(60ms)"
		if line.attrName == "capacity":
			tmp.yLabel = "cap/mbps"
		tmp.x = line.x
		tmp.y = line.y
		tmp.yLineLabel = self.traceName
		tmp.figSavePath = figSavePath
		return tmp
