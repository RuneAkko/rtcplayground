import glob
import os.path
import random

import numpy as np
from fitter import Fitter
from matplotlib import pyplot as plt
from scipy.signal import savgol_filter
import scipy.stats as st
from utils.trace import Trace, TracePattern


def traceHistFitCap(sample: Trace, figpath):
	resultTmp = sample.traceName + " " + "best fit\n"
	
	x = [x.capacity for x in sample.tracePatterns]
	# x = savgol_filter(x, 11, 4, mode="nearest")
	
	fer = Fitter(list(x), timeout=30)
	fer.fit(progress=True)
	
	m = fer.get_best()
	resultTmp += str(m) + "\n"
	(name, _), = m.items()
	resultTmp += str(fer.summary(Nbest=3, plot=True)) + "\n"
	plt.savefig(figpath + "FitCap " + sample.traceName)
	plt.close()
	return resultTmp


def orifit():
	traceFiles = glob.glob("/Users/hansenma/mhspion/rtcplayground/mytraces/ori_traces_preprocess/*.json",
	                       recursive=False)
	figSavePath = "/Users/hansenma/mhspion/rtcplayground/mytraces/traceFig/"
	
	result = ""
	for ele in traceFiles:
		t = Trace(ele)
		t.readTraceFile()
		res = traceHistFitCap(t, figSavePath)
		result += res + "\n"
	
	with open("/Users/hansenma/mhspion/rtcplayground/mytraces/fit_result.txt", "w") as f:
		f.write(result)


def dealWithTrace(savePath="/Users/hansenma/mhspion/rtcplayground/mytraces/ori_traces_preprocess/",
                  file="/Users/hansenma/mhspion/rtcplayground/mytraces/ori_traces/*.json"
                  ):
	savePath = savePath
	traceFiles = glob.glob(file,
	                       recursive=False)
	for ele in traceFiles:
		t = Trace(ele)
		t.readTraceFile()
		t.draw(t.genFig(savePath, t.genLine("capacity")))


# t.preFilter()
# t.filterForTime()
# t.writeTraceFile(savePath)


def genNewTrace(storePath, trace_num):
	traceDict = {
		
		"5G_13mbps": {
			"params": (1.536302827753233, 14700.000000000144, 1561.688230475725)
		},
		"5G_12mbps": {
			"params": (13742.030804318989, 1227.6995870545934)
		},
		"4G_700kbps": {
			"params": (1.425999818712874, 648.7758308425668, 230.88861573132255)
		},
		"WIRED_200kbps": {
			"params": (180.47698720367868, 13.020194936661813)
		},
		"4G_500kbps": {
			"params": (499.31064150943394, 198.31335141487523)
		},
		"WIRED_900kbs": {
			"params": (864.3000516042639, 53.4175785243462)
		},
		"WIRED_35mbps": {
			"params": (33900.0, 13974.62621885157)
		},
		"4G_3mbps": {
			"params": (403.85196271362327, 3152.3062735940803)
		}
		
	}
	
	time_step = 240  # ms
	
	trace_size = 1500  # trace 为 300 second
	
	for k, v in traceDict.items():
		traceName = k
		params = v["params"]
		
		num = 0
		while num < trace_num:
			num += 1
			
			capData = None  # kbps
			trace = Trace()
			trace.traceName = traceName + "_generate_No_" + str(num)
			
			if traceName == "5G_13mbps":
				capData = st.laplace_asymmetric.rvs(*params, size=trace_size)
			if traceName == "5G_12mbps":
				capData = st.cauchy.rvs(*params, trace_size)
			if traceName == "4G_700kbps":
				capData = st.dweibull.rvs(*params, trace_size)
			if traceName == "WIRED_200kbps":
				capData = st.cauchy.rvs(*params, trace_size)
			if traceName == "4G_500kbps":
				capData = st.norm.rvs(*params, trace_size)
			if traceName == "WIRED_900kbs":
				capData = st.logistic.rvs(*params, trace_size)
			if traceName == "WIRED_35mbps":
				capData = st.laplace.rvs(*params, trace_size)
			if traceName == "4G_3mbps":
				capData = st.rayleigh.rvs(*params, trace_size)
			
			capData = list(capData)
			random.shuffle(capData)
			
			aver = np.mean(capData)
			data = []
			
			for ele in capData:
				if ele < 0:
					continue
				if ele < aver / 3:
					continue
				
				data.append(ele)
			
			for ele in data:
				traceP = TracePattern()
				traceP.duration = time_step
				traceP.capacity = ele
				trace.tracePatterns.append(traceP)
			
			trace.preFilter()
			trace.filterForTime()
			trace.writeTraceFile(storePath)


def genNewTraceTrain():
	newTracePath = "/Users/hansenma/mhspion/rtcplayground/mytraces/trainTraces/"
	if not os.path.exists(newTracePath):
		os.mkdir(newTracePath)
	trace_num = 100
	genNewTrace(newTracePath, trace_num)


def genNewTraceTest():
	newTracePath = "/Users/hansenma/mhspion/rtcplayground/mytraces/testTraces/"
	if not os.path.exists(newTracePath):
		os.mkdir(newTracePath)
	trace_num = 1
	genNewTrace(newTracePath, trace_num)


if __name__ == "__main__":
	genNewTraceTrain()
# f = "/Users/hansenma/mhspion/rtcplayground/mytraces/testTraces/*.json"
# ff = "/Users/hansenma/mhspion/rtcplayground/mytraces/testTraces"
# dealWithTrace(ff, f)
# genNewTraceTest()
