import glob

import numpy as np
import torch
from scipy.signal import savgol_filter
import numpy as np

from deep_rl.actor_critic import ActorCritic
from offlineStatTest import writeStatsReports
from rtc_env import GymEnv
from rtc_env import log_to_linear
from utils.plotTool import Line, drawLine, drawScatter
from utils.trace import Trace


def drlEstimatorTest(tracePath, modelPath):
	estimationName = "drl"
	env = GymEnv()
	env.setAlphaRtcGym(tracePath)
	
	trace = Trace(traceFilePath=tracePath)
	trace.readTraceFile()
	# trace.preFilter()
	trace.filterForTime()
	traceName, tracePatterns = trace.traceName, trace.tracePatterns
	
	state_dim = 5
	model = ActorCritic(state_dim, 1, exploration_param=0.05)
	model.load_state_dict(torch.load(modelPath))
	
	max_step = 100000
	step = 0
	stepList = []
	recvList = []
	delayList = []
	lossList = []
	targetRate = []
	done = False
	state = torch.Tensor([0.0 for _ in range(state_dim)])
	while not done and step < max_step:
		action, _, _ = model.forward(state)
		state, reward, done, _ = env.step(action, step)
		targetRate.append(log_to_linear(action))
		recvList.append(log_to_linear(state[0]))
		delayList.append(state[1])
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
	drawLine(dirName, gccRate, recvRate, traceCap)
	drawLine(dirName, delayCurve)
	drawLine(dirName, lossCurve)


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
	
	digLogV2 = [[0, 0, 0]]
	
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
			digLogV2.append(
				[env.ruleEstimator.gcc.rateController.average_max_rate_kbps,
				 env.ruleEstimator.gcc.rateController.average_max_rate_kbps_std,
				 env.ruleEstimator.gcc.rateController.rateHatKbps]
			)
		
		if estimatorTag == 1:
			gamma.append(env.geminiEstimator.gcc_rate_controller.trendline_estimator.trendline * 4)
			queueDelayDelta.append(env.geminiEstimator.gcc_rate_controller.detector.T)
	
	dirName = "fig"
	
	gccRate = genLineV2(stepList, [x / 1000 for x in targetRate], traceName + "-gccRate" + "-" + estimationName)
	recvRate = genLineV2(stepList, [x / 1000 for x in recvList], traceName + "-recvRate" + "-" + estimationName)
	delayCurve = genLineV2(stepList, delayList, traceName + "-delay-" + estimationName)
	lossCurve = genLineV2(stepList, lossList, traceName + "-loss-" + estimationName)
	
	traceCap = trace.genLine("capacity", smooth=False)
	
	drawLine(dirName, traceCap, recvRate, gccRate)
	drawLine(dirName, delayCurve)
	drawLine(dirName, lossCurve)
	
	gammaLine = genLineV2(stepList, gamma, traceName + "-threshold" + "-" + estimationName)
	gammaNegativeLine = genLineV2(stepList, [x * -1 for x in gamma], traceName + "-threshold" + "-" + estimationName)
	queueDelayDeltaLine = genLineV2(stepList, prefilter(queueDelayDelta), traceName + "-esimate-" + estimationName)
	drawLine(dirName, gammaLine, queueDelayDeltaLine, gammaNegativeLine)
	drawLine(dirName, queueDelayDeltaLine)
	
	gccStateLine = genLineV2(stepList, gccState, traceName + "-gccState-" + estimationName)
	drawScatter(dirName, gccStateLine)
	
	average_max_rate = genLineV2(stepList, [x[0] for x in digLogV2],
	                             traceName + "-average_max_rate" + "-" + estimationName)
	average_max_rate_bound_up = genLineV2(stepList, [x[0] + 3 * x[1] for x in digLogV2],
	                                      traceName + "-bound_up" + "-" + estimationName)
	average_max_rate_bound_down = genLineV2(stepList, [x[0] - 3 * x[1] for x in digLogV2],
	                                        traceName + "-bound_down" + "-" + estimationName)
	rateHat = genLineV2(stepList, [x[2] for x in digLogV2], traceName + "-rateHat" + "-" + estimationName)
	
	drawLine(dirName, average_max_rate, average_max_rate_bound_up, average_max_rate_bound_down, rateHat)


# netDataSavePath = "./netData/" + traceName + "_netData" + "_" + estimationName
# writeStatsReports(netDataSavePath, netDataList)
# netDataSavePath = "./netData/" + traceName + "_netData" + "_" + estimationName
# writeStatsReports(netDataSavePath, netDataList)
def genLineV2(x, y, name, smooth=False) -> Line:
	tmp = Line()
	tmp.name = name
	tmp.x = x
	if smooth:
		y = savgol_filter(y, 21, 4, mode="nearest")
	tmp.y = y
	return tmp


def prefilter(y):
	y1 = np.abs(y)
	mediaQ = np.median(y1)
	# last = 0
	for i, v in enumerate(y):
		if abs(v) > 10 * mediaQ:
			y[i] = 10 * mediaQ
	# last = y[i]
	return y


# traceFiles = glob.glob(f"./mytraces/ori_traces_preprocess/*.json", recursive=False)
traceFiles = glob.glob(f"./mytraces/specialTrace/03.json", recursive=False)

models = "./model/ppo_2022_04_10_04_53_52.pth"
for ele in traceFiles:
	estimatorTest(ele, 0)
# for ele in traceFiles:
# 	estimatorTest(ele, 1)
# for ele in traceFiles:
# # 	estimatorTest(ele, 1)
# for ele in traceFiles:
# 	drlEstimatorTest(ele, models)
