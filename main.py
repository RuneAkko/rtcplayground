import glob

from offlineStatTest import writeStatsReports
from plot.drawCurve import Line
from plot.drawCurve import draw
from rtc_env import GymEnv
from utils.trace_analyse import readTrace, preprocess


def scaleTraceCap(tracePath) -> Line:
	traceName, ts = readTrace(tracePath)
	ts = preprocess(ts)
	traceCap = Line()
	y = [tmp.capacity for tmp in ts]
	x = [tmp.time / 60 for tmp in ts]
	traceCap.x = x
	traceCap.y = y
	return traceCap


def estimatorTest(tracePath, estimatorTag):
	if estimatorTag == 0:
		estimationName = "OwnGCC"
		testversion = "1"
	else:
		estimationName = "GeminiGCC"
		testversion = "2"
	
	env = GymEnv()
	traceName, tracePatterns = readTrace(tracePath)
	
	env.set(tracePath)
	
	max_step = 100000
	traceDone = False
	step = 0
	
	recvList = [0]
	stepList = [step]
	delayList = [0]
	
	rate = env.lastBwe
	
	targetRate = [rate]
	netDataList = []
	
	while not traceDone and step < max_step:
		if estimatorTag == 0:
			rate, traceDone, recvRate, delay, qos3, qos4, netData = env.testV1(rate)
		else:
			rate, traceDone, recvRate, delay, qos3, qos4, netData = env.testV2(rate)
		recvList.append(recvRate)
		step += 1
		stepList.append(step)
		delayList.append(delay)
		targetRate.append(rate)
		netDataList.append(netData)
	
	capCurve = scaleTraceCap(tracePath)
	
	gccRate = Line()
	gccRate.name = traceName + "-gccRate" + "-" + estimationName
	gccRate.x = stepList
	gccRate.y = [x / 1000000 for x in targetRate]  # mbps
	
	recvRate = Line()
	recvRate.name = traceName + "-recvRate" + "-" + estimationName
	recvRate.x = stepList
	recvRate.y = [x / 1000000 for x in recvList]  # mbps
	
	delayCurve = Line()
	delayCurve.name = traceName + "-delay-" + estimationName
	delayCurve.x = stepList
	delayCurve.y = delayList
	
	draw(traceName + "-" + estimationName, gccRate, recvRate, capCurve)
	draw(traceName + "-" + estimationName, delayCurve)
	
	netDataSavePath = "./netData/" + traceName + "_netData" + "_" + estimationName
	writeStatsReports(netDataSavePath, netDataList)


traceFiles = glob.glob(f"./traces/*.json")
for ele in traceFiles:
	estimatorTest(ele, "0")
for ele in traceFiles:
	estimatorTest(ele, "1")
