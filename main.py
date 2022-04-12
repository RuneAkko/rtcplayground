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
	# trace.preFilter()
	# trace.filterForTime()
	traceName, tracePatterns = trace.traceName, trace.tracePatterns
	
	model = ActorCritic(5, 1, exploration_param=0.05)
	model.load_state_dict(torch.load(modelPath))
	
	max_step = 100000
	step = 0
	stepList = []
	recvList = []
	delayList = []
	lossList = []
	targetRate = []
	done = False
	state = torch.Tensor([0.0 for _ in range(5)])
	while not done and step < max_step:
		action, _, _ = model.forward(state)
		state, reward, done, _ = env.step(action)
		targetRate.append(log_to_linear(action))
		recvList.append(log_to_linear(state[0]))
		delayList.append(state[1] * 2 * 1000)
		lossList.append(state[2])
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
	
	delayCurve = Line()
	delayCurve.name = traceName + "-delay-" + estimationName
	delayCurve.x = stepList
	delayCurve.y = delayList
	# delayCurve.y = savgol_filter(delayCurve.y, 20, 1, mode="nearest")
	
	lossCurve = Line()
	lossCurve.name = traceName + "-loss-" + estimationName
	lossCurve.x = stepList
	lossCurve.y = lossList
	
	traceCap = trace.genLine("capacity", smooth=False)
	drawLine(dirName, traceName + "-rate-" + estimationName, gccRate, recvRate, traceCap)
	drawLine(dirName, traceName + "-delay-" + estimationName, delayCurve)
	drawLine(dirName, traceName + "-loss-" + estimationName, lossCurve)


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
	lossList = [0]
	
	rate = env.lastBwe
	
	targetRate = [rate]
	netDataList = []
	
	# ==================== dig gcc internal args
	queueDelayDelta = [0]
	gamma = [0]
	gccState = [0]  # -1:decrease, 0:hold,1:increase-add,2:increase-mult
	
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
		lossList.append(qos3)
		
		if estimatorTag == 0:
			queueDelayDelta.append(env.ruleEstimator.gcc.queueDelayDelta)
			gamma.append(env.ruleEstimator.gcc.overUseDetector.adaptiveThreshold.thresholdGamma)
			gccState.append(env.ruleEstimator.gcc.rateController.digLog)
		if estimatorTag == 1:
			gamma.append(env.geminiEstimator.gcc_rate_controller.trendline_estimator.trendline * 4)
			queueDelayDelta.append(env.geminiEstimator.gcc_rate_controller.detector.T)
	
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
	# recvRate.y = savgol_filter(recvRate.y, 21, 4, mode="nearest")
	
	delayCurve = Line()
	delayCurve.name = traceName + "-delay-" + estimationName
	delayCurve.x = stepList
	delayCurve.y = delayList
	# delayCurve.y = savgol_filter(delayCurve.y, 20, 1, mode="nearest")
	
	lossCurve = Line()
	lossCurve.name = traceName + "-delay-" + estimationName
	lossCurve.x = stepList
	lossCurve.y = lossList
	
	traceCap = trace.genLine("capacity", smooth=False)
	
	drawLine(dirName, traceName + "-rate-" + estimationName, traceCap, recvRate, gccRate)
	drawLine(dirName, traceName + "-delay-" + estimationName, delayCurve)
	drawLine(dirName, traceName + "-loss-" + estimationName, lossCurve)
	
	# netDataSavePath = "./netData/" + traceName + "_netData" + "_" + estimationName
	# writeStatsReports(netDataSavePath, netDataList)
	# netDataSavePath = "./netData/" + traceName + "_netData" + "_" + estimationName
	# writeStatsReports(netDataSavePath, netDataList)
	
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
	
	drawLine(dirName, traceName + "-esimate-" + estimationName, queueDelayDeltaLine)
	
	gccStateLine = Line()
	gccStateLine.name = traceName + "-gccState-" + estimationName
	gccStateLine.x = stepList
	gccStateLine.y = gccState
	
	drawLine(dirName, traceName + "-esimate-" + estimationName, gccStateLine)


# traceFiles = glob.glob(f"./mytraces/ori_traces_preprocess/*.json", recursive=False)
traceFiles = glob.glob(f"./mytraces/specialTrace/*.json", recursive=False)

models = "./model/ppo_2022_04_10_04_53_52.pth"
for ele in traceFiles:
	estimatorTest(ele, 0)
for ele in traceFiles:
	estimatorTest(ele, 1)
# for ele in traceFiles:
# # 	estimatorTest(ele, 1)
# for ele in traceFiles:
# 	drlEstimatorTest(ele, models)
