import glob

from offlineStatTest import writeStatsReports
from plot.drawCurve import Line
from plot.drawCurve import draw
from rtc_env import GymEnv
from utils.trace_analyse import readTrace, preprocess


def ruleEstimatorTest(tracePath):
	estimationName = "OwnGCC"
	env = GymEnv()
	traceName, tracePatterns = readTrace(tracePath)
	
	env.set(tracePath)
	
	max_step = 100000
	traceDone = False
	step = 0
	
	qosList = [0]
	stepList = [step]
	
	rate = env.ruleEstimator.predictionBandwidth
	targetRate = [rate]
	netDataList = []
	
	while not traceDone and step < max_step:
		rate, traceDone, recvRate, qos2, qos3, qos4, netData = env.testV1(rate)
		qosList.append(recvRate)
		step += 1
		stepList.append(step)
		targetRate.append(rate)
		netDataList.append(netData)
	
	tracePatterns = preprocess(tracePatterns)
	capCurve = Line()
	
	gccRate = Line()
	gccRate.name = traceName + "-gccRate" + "-" + estimationName
	gccRate.x = stepList
	gccRate.y = [x / 1000000 for x in targetRate]  # mbps
	
	recvRate = Line()
	recvRate.name = traceName + "-recvRate" + "-" + estimationName
	recvRate.x = stepList
	recvRate.y = [x / 1000000 for x in qosList]  # mbps
	
	draw(traceName, gccRate, recvRate)
	
	# with open(name + "-testGccRate", "w") as f:
	# 	f.write(str(gccRate.y))
	# with open(name + "-testRecvRate", "w") as f:
	# 	f.write(str(recvRate.y))
	
	netDataSavePath = "./netData/" + traceName + "_netData" + "_" + estimationName
	writeStatsReports(netDataSavePath, netDataList)


def geminiEstimatorTest(tracePath):
	estimationName = "GeminiGCC"
	env = GymEnv()
	traceName, tracePatterns = readTrace(tracePath)
	
	env.set(tracePath)
	
	max_step = 100000
	traceDone = False
	step = 0
	
	qosList = [0]
	stepList = [step]
	
	rate = env.ruleEstimator.predictionBandwidth
	targetRate = [rate]
	netDataList = []
	
	while not traceDone and step < max_step:
		rate, traceDone, recvRate, qos2, qos3, qos4, netData = env.testV2(rate)
		qosList.append(recvRate)
		step += 1
		stepList.append(step)
		targetRate.append(rate)
		netDataList.append(netData)
	
	tracePatterns = preprocess(tracePatterns)
	capCurve = Line()
	
	gccRate = Line()
	gccRate.name = traceName + "-gccRate" + "-" + estimationName
	gccRate.x = stepList
	gccRate.y = [x / 1000000 for x in targetRate]  # mbps
	
	recvRate = Line()
	recvRate.name = traceName + "-recvRate" + "-" + estimationName
	recvRate.x = stepList
	recvRate.y = [x / 1000000 for x in qosList]  # mbps
	
	draw(traceName, gccRate, recvRate)
	
	# with open(name + "-testGccRate", "w") as f:
	# 	f.write(str(gccRate.y))
	# with open(name + "-testRecvRate", "w") as f:
	# 	f.write(str(recvRate.y))
	
	netDataSavePath = "./netData/" + traceName + "_netData" + "_" + estimationName
	writeStatsReports(netDataSavePath, netDataList)


traceFiles = glob.glob(f"./traces/*.json")
for ele in traceFiles:
	ruleEstimatorTest(ele)
for ele in traceFiles:
	geminiEstimatorTest(ele)
