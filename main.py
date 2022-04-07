import glob

import torch
from scipy.signal import savgol_filter

from deep_rl.actor_critic import ActorCritic
from offlineStatTest import writeStatsReports
from plot.plotTool import Line, drawLine
from rtc_env import GymEnv
from rtc_env import log_to_linear
from utils.trace_analyse import genTraceCap
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


def drlEstimatorTest(tracePath, modelPath):
	estimationName = "drl"
	env = GymEnv()
	env.setAlphaRtcGym(tracePath)
	traceName, tracePatterns = readTrace(tracePath)
	
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
	gccRate.y = [x / 1000000 for x in targetRate]  # mbps
	gccRate.y = savgol_filter(gccRate.y, 21, 1, mode="nearest")
	
	recvRate = Line()
	recvRate.name = traceName + "-recvRate" + "-" + estimationName
	recvRate.x = stepList
	recvRate.y = [x / 1000000 for x in recvList]  # mbps
	recvRate.y = savgol_filter(recvRate.y, 21, 1, mode="nearest")
	
	# delayCurve = Line()
	# delayCurve.name = traceName + "-delay-" + estimationName
	# delayCurve.x = stepList
	# delayCurve.y = delayList
	# delayCurve.y = savgol_filter(delayCurve.y, 20, 1, mode="nearest")
	
	traceCap = genTraceCap(tracePath)
	
	drawLine(dirName, traceName + "-rate-" + estimationName, gccRate, recvRate, traceCap)


def estimatorTest(tracePath, estimatorTag):
	if estimatorTag == 0:
		estimationName = "OwnGCC"
		testversion = "1"
	else:
		estimationName = "GeminiGCC"
		testversion = "2"
	
	env = GymEnv()
	env.setAlphaRtcGym(tracePath)
	traceName, tracePatterns = readTrace(tracePath)
	
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
	
	dirName = "fig"
	
	capCurve = scaleTraceCap(tracePath)
	
	gccRate = Line()
	gccRate.name = traceName + "-gccRate" + "-" + estimationName
	gccRate.x = stepList
	gccRate.y = [x / 1000000 for x in targetRate]  # mbps
	gccRate.y = savgol_filter(gccRate.y, 20, 1, mode="nearest")
	
	recvRate = Line()
	recvRate.name = traceName + "-recvRate" + "-" + estimationName
	recvRate.x = stepList
	recvRate.y = [x / 1000000 for x in recvList]  # mbps
	recvRate.y = savgol_filter(recvRate.y, 20, 1, mode="nearest")
	
	delayCurve = Line()
	delayCurve.name = traceName + "-delay-" + estimationName
	delayCurve.x = stepList
	delayCurve.y = delayList
	delayCurve.y = savgol_filter(delayCurve.y, 20, 1, mode="nearest")
	
	traceCap = genTraceCap(tracePath)
	
	drawLine(dirName, traceName + "-rate-" + estimationName, gccRate, recvRate, traceCap)
	drawLine(dirName, traceName + "-delay-" + estimationName, delayCurve)
	
	netDataSavePath = "./netData/" + traceName + "_netData" + "_" + estimationName
	writeStatsReports(netDataSavePath, netDataList)


traceFiles = glob.glob(f"mytraces/*.json", recursive=False)
model = "./model/ppo_2021_05_13_01_55_53.pth"
# for ele in traceFiles:
# 	estimatorTest(ele, 0)
# for ele in traceFiles:
# 	estimatorTest(ele, 1)
for ele in traceFiles:
	drlEstimatorTest(ele,model)
