import glob

from offlineStatTest import writeStatsReports
from plot.drawCurve import Line
from plot.drawCurve import draw
from rtc_env import GymEnv
from utils.trace_analyse import getTrace


def ruleEstimatorTest(path):
	"""
	:return:
	"""
	env = GymEnv()
	name, _ = getTrace(path)
	env.set(path)
	
	max_step = 100000
	traceDone = False
	step = 0
	
	qosList = [0]
	stepList = [step]
	
	rate = env.ruleEstimator.predictionBandwidth
	targetRate = [rate]
	netDataList = []
	
	while not traceDone and step < max_step:
		rate, traceDone, qos1, qos2, qos3, qos4, netData = env.test(rate, step)
		qosList.append(qos1)
		step += 1
		stepList.append(step)
		targetRate.append(rate)
		netDataList.append(netData)
	
	# realRate = Line()
	# realRate.name = "cap"
	gccRate = Line()
	gccRate.name = name + "-gccRate"
	gccRate.x = stepList
	gccRate.y = [x / 1000000 for x in targetRate]  # mbps
	
	recvRate = Line()
	recvRate.name = name + "-recvRate"
	recvRate.x = stepList
	recvRate.y = [x / 1000000 for x in qosList]  # mbps
	
	draw(name, gccRate, recvRate)
	# draw(recvRate)
	
	# with open(name + "-testGccRate", "w") as f:
	# 	f.write(str(gccRate.y))
	# with open(name + "-testRecvRate", "w") as f:
	# 	f.write(str(recvRate.y))
	
	netDataSavePath = "./netData/" + name + "_netData"
	writeStatsReports(netDataSavePath, netDataList)


traceFiles = glob.glob(f"./traces/*.json")
for ele in traceFiles:
	ruleEstimatorTest(ele)
