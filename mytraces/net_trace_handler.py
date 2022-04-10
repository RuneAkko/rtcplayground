import glob

from fitter import Fitter
from matplotlib import pyplot as plt
from scipy.signal import savgol_filter
import scipy.stats as st
from utils.trace import Trace, TracePattern


def traceHistFitCap(sample: Trace, figpath):
	resultTmp = sample.traceName + " " + "best fit\n"
	
	x = [x.capacity for x in sample.tracePatterns]
	x = savgol_filter(x, 11, 4, mode="nearest")
	
	fer = Fitter(list(x), timeout=10)
	fer.fit(progress=True)
	
	m = fer.get_best()
	resultTmp += str(m) + "\n"
	(name, _), = m.items()
	resultTmp += str(fer.summary(Nbest=3, plot=True)) + "\n"
	plt.savefig(figpath + "Fit " + sample.traceName)
	plt.close()
	return resultTmp


def orifit():
	traceFiles = glob.glob("/Users/hansenma/mhspion/rtcplayground/mytraces/ori_traces/*.json", recursive=False)
	figSavePath = "/Users/hansenma/mhspion/rtcplayground/mytraces/traceFig/"
	
	result = ""
	for ele in traceFiles:
		t = Trace(ele)
		t.readTraceFile()
		t.preFilter()
		res = traceHistFitCap(t, figSavePath)
		result += res + "\n"
	
	with open("/Users/hansenma/mhspion/rtcplayground/mytraces/fit_result.txt", "w") as f:
		f.write(result)


def drawTraceCap(figSavePath="/Users/hansenma/mhspion/rtcplayground/mytraces/traceFig/",
                 file="/Users/hansenma/mhspion/rtcplayground/mytraces/ori_traces/*.json"
                 ):
	figSavePath = figSavePath
	traceFiles = glob.glob(file,
	                       recursive=False)
	for ele in traceFiles:
		t = Trace(ele)
		t.readTraceFile()
		t.preFilter()
		traceFig = t.genFig(figSavePath, t.genLine("capacity", smooth=True))
		t.draw(traceFig)


def readTraceCap(file):
	traceFiles = glob.glob(file,
	                       recursive=False)
	for ele in traceFiles:
		t = Trace(ele)
		t.readTraceFile()
		t.preFilter()
		for ele in t.tracePatterns:
			if ele.capacity * 1000 < 50:
				print(ele.capacity)


def oriSmooth():
	traceFiles = glob.glob("/Users/hansenma/mhspion/rtcplayground/mytraces/ori_traces/*.json", recursive=False)
	newTracePath = "/Users/hansenma/mhspion/rtcplayground/mytraces/ori_traces_smooth/"
	for ele in traceFiles:
		t = Trace(ele)
		t.readTraceFile()
		t.preFilter()
		t.newTracePatterns = t.tracePatterns
		t.writeTraceFile(newTracePath)


def genNewTrace(storePath, num):
	newTracePath = storePath
	trace_num = num
	
	traceDict = {
		
		"5G_13mbps": {
			"params": (-3.772561933925422, 15.786516291709393, 15.786516291709393)
		},
		"5G_12mbps": {
			"params": (0.3663911644658445, 14.045197074416883, 1.0383217938517015)
		},
		"4G_700kbps": {
			"params": (0.6853110588522835, 0.19583240621158454)
		},
		"WIRED_200kbps": {
			"params": (0.8772432983855415, 0.20739160839162063, 0.03491181250348681)
		},
		"4G_500kbps": {
			"params": (0.49803766512735487, 0.17471835822945928)
		},
		"WIRED_900kbs": {
			"params": (1.4851068818865092, 0.8665280703466564, 0.017731250635105254)
		},
		"WIRED_35mbps": {
			"params": (0.35861538997769365, 34.23464481724227, 2.8567367471823966)
		},
		"4G_3mbps": {
			"params": (3.3348407830697964, 0.8356698606071555, 2.536367226903189)
		}
		
	}
	time_step = 200  # ms
	
	trace_size = 5000  # trace 为 300 second
	
	for k, v in traceDict.items():
		traceName = k
		params = v["params"]
		
		num = 0
		while num < trace_num:
			num += 1
			
			capData = None
			trace = Trace()
			trace.traceName = traceName + "_" + str(num)
			if traceName == "5G_13mbps":
				capData = st.skewnorm.rvs(*params, size=trace_size)
			if traceName == "5G_12mbps":
				capData = st.genlogistic.rvs(*params, trace_size)
			if traceName == "4G_700kbps":
				capData = st.cosine.rvs(*params, trace_size)
			if traceName == "WIRED_200kbps":
				capData = st.dgamma.rvs(*params, trace_size)
			if traceName == "4G_500kbps":
				capData = st.norm.rvs(*params, trace_size)
			if traceName == "WIRED_900kbs":
				capData = st.dgamma.rvs(*params, trace_size)
			if traceName == "WIRED_35mbps":
				capData = st.tukeylambda.rvs(*params, trace_size)
			if traceName == "4G_3mbps":
				capData = st.skewnorm.rvs(*params, trace_size)
			capData = list(capData)
			data = []
			for ele in capData:
				if ele < 0:
					continue
				data.append(ele)
			data = trace.smooth(data)
			
			for ele in data:
				traceP = TracePattern()
				traceP.duration = time_step
				traceP.capacity = ele
				trace.tracePatterns.append(traceP)
			trace.writeTraceFile(newTracePath)


def genNewTraceTrain():
	newTracePath = "/Users/hansenma/mhspion/rtcplayground/mytraces/trainTraces/"
	trace_num = 100
	genNewTrace(newTracePath, trace_num)


def genNewTraceTest():
	newTracePath = "/Users/hansenma/mhspion/rtcplayground/mytraces/testTraces/"
	trace_num = 1
	genNewTrace(newTracePath, trace_num)


if __name__ == "__main__":
	genNewTraceTest()
# genNewTraceTrain()
# readTraceCap("/Users/hansenma/mhspion/rtcplayground/mytraces/trainTraces/*.json")
