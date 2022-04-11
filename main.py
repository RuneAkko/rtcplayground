import glob

import torch
from scipy.signal import savgol_filter

from deep_rl.actor_critic import ActorCritic
from offlineStatTest import writeStatsReports
from rtc_env import GymEnv
from rtc_env import log_to_linear
from utils.plotTool import Line, drawLine
from utils.trace import Trace


def drlEstimatorTest(tracePath, modelPath):
	estimationName = "drl"
	env = GymEnv()
	env.setAlphaRtcGym(tracePath)
	
	trace = Trace(traceFilePath=tracePath)
	trace.readTraceFile()
	trace.preFilter()
	trace.filterForTime()
	traceName, tracePatterns = trace.traceName, trace.tracePatterns
	
	model = ActorCritic(5, 1, exploration_param=0.05)
	model.load_state_dict(torch.load(modelPath))
	
	max_step = 100000
	step = 0
	stepList = []
	recvList = []
	targetRate = []
	done = False
	state = torch.Tensor([0.0 for _ in range(5)])
	while not done and step < max_step:
		action, _, _ = model.forward(state)
		state, reward, done, _ = env.step(action)
		targetRate.append(log_to_linear(action))
		recvList.append(log_to_linear(state[0]))
		state = torch.Tensor(state)
		stepList.append(step)
		step += 1
	
	dirName = "fig"
	
	gccRate = Line()
	gccRate.name = traceName + "-gccRate" + "-" + estimationName
	gccRate.x = stepList
	gccRate.y = [x / 1000 for x in targetRate]  # kbps
	# gccRate.y = savgol_filter(gccRate.y, 21, 1, mode="nearest")
	
	recvRate = Line()
	recvRate.name = traceName + "-recvRate" + "-" + estimationName
	recvRate.x = stepList
	recvRate.y = [x / 1000 for x in recvList]  # kbps
	# recvRate.y = savgol_filter(recvRate.y, 21, 1, mode="nearest")
	
	# delayCurve = Line()
	# delayCurve.name = traceName + "-delay-" + estimationName
	# delayCurve.x = stepList
	# delayCurve.y = delayList
	# delayCurve.y = savgol_filter(delayCurve.y, 20, 1, mode="nearest")
	
	traceCap = trace.genLine("capacity", smooth=False)
	
	drawLine(dirName, traceName + "-rate-" + estimationName, gccRate, traceCap)


def estimatorTest(tracePath, estimatorTag):
	if estimatorTag == 0:
		estimationName = "OwnGCC"
		testversion = "1"
	else:
		estimationName = "GeminiGCC"
		testversion = "2"
	
	env = GymEnv()
	env.setAlphaRtcGym(tracePath)
	trace = Trace(traceFilePath=tracePath)
	trace.readTraceFile()
	trace.preFilter()
	trace.filterForTime()
	
	traceName, tracePatterns = trace.traceName, trace.tracePatterns
	
	max_step = 100000
	traceDone = False
	step = 0
	
	recvList = [0]
	stepList = [step]
	delayList = [0]
	
	rate = env.lastBwe
	
	targetRate = [rate]
	netDataList = []
	
	# ==================== dig gcc internal args
	queueDelayDelta = []
	gamma = []
	
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
		
		if estimatorTag == 0:
			queueDelayDelta.append(env.ruleEstimator.gcc.queueDelayDelta)
			gamma.append(env.ruleEstimator.gcc.overUseDetector.adaptiveThreshold.thresholdGamma)
	
	dirName = "fig"
	
	gccRate = Line()
	gccRate.name = traceName + "-gccRate" + "-" + estimationName
	gccRate.x = stepList
	gccRate.y = [x / 1000 for x in targetRate]  # kbps
	# gccRate.y = savgol_filter(gccRate.y, 20, 1, mode="nearest")
	
	recvRate = Line()
	recvRate.name = traceName + "-recvRate" + "-" + estimationName
	recvRate.x = stepList
	recvRate.y = [x / 1000 for x in recvList]  # kbps
	# recvRate.y = savgol_filter(recvRate.y, 20, 1, mode="nearest")
	
	delayCurve = Line()
	delayCurve.name = traceName + "-delay-" + estimationName
	delayCurve.x = stepList
	delayCurve.y = delayList
	# delayCurve.y = savgol_filter(delayCurve.y, 20, 1, mode="nearest")
	
	traceCap = trace.genLine("capacity", smooth=False)
	
	drawLine(dirName, traceName + "-rate-" + estimationName, gccRate, traceCap)
	drawLine(dirName, traceName + "-delay-" + estimationName, delayCurve)
	
	if estimatorTag != 0:
		return
	
	gammaNegative = [x * -1 for x in gamma]
	gammaLine, gammaNegativeLine, queueDelayDeltaLine = Line(), Line(), Line()
	gammaLine.name = traceName + "-gamma" + "-" + estimationName
	gammaLine.x = stepList
	gammaLine.y = gamma
	
	gammaNegativeLine.name = traceName + "-gamma" + "-" + estimationName
	gammaNegativeLine.x = stepList
	gammaNegativeLine.y = gammaNegative
	
	queueDelayDeltaLine.name = traceName + "-delay" + "-" + estimationName
	queueDelayDeltaLine.x = stepList
	queueDelayDeltaLine.y = queueDelayDelta
	
	drawLine(dirName, traceName + "-threshold-" + estimationName, gammaLine, queueDelayDeltaLine, gammaNegativeLine)


# ==================== dig gcc internal args


# netDataSavePath = "./netData/" + traceName + "_netData" + "_" + estimationName
# writeStatsReports(netDataSavePath, netDataList)


traceFiles = glob.glob(f"./mytraces/specialTrace/*.json", recursive=False)
models = "./model/ppo_2022_04_10_04_53_52.pth"
for ele in traceFiles:
	estimatorTest(ele, 0)
# for ele in traceFiles:
# 	estimatorTest(ele, 1)
# for ele in traceFiles:
# 	drlEstimatorTest(ele, models)
