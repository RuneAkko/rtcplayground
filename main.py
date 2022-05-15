import glob

import matplotlib.pyplot as plt
import numpy as np
import torch
from scipy.signal import savgol_filter
import numpy as np
import os
from deep_rl.actor_critic import ActorCritic
from offlineStatTest import writeStatsReports
from rtc_env import GymEnv
from rtc_env import log_to_linear
from utils.plotTool import Line, drawLine, drawScatter
from utils.trace import Trace

# if estimatorTag == 0:
# 	gccStateLine = genLineV2(stepList, gccState, traceName + "-gccState-" + estimationName)
# 	drawScatter(dirNamePicture, gccStateLine)
#
# 	average_max_rate = genLineV2(stepList, [x[0] for x in digLogV2],
# 	                             traceName + "-average_max_rate" + "-" + estimationName)
# 	average_max_rate_bound_up = genLineV2(stepList, [x[0] + 3 * x[1] for x in digLogV2],
# 	                                      traceName + "-bound_up" + "-" + estimationName)
# 	average_max_rate_bound_down = genLineV2(stepList, [x[0] - 3 * x[1] for x in digLogV2],
# 	                                        traceName + "-bound_down" + "-" + estimationName)
#
# 	rateHat = genLineV2(stepList, [x[2] for x in digLogV2], traceName + "-rateHat" + "-" + estimationName)
#
# 	drawLine(dirNamePicture, dirNameDate, average_max_rate, average_max_rate_bound_up, average_max_rate_bound_down,
# 	         rateHat)


# netDataSavePath = "./netData/" + traceName + "_netData" + "_" + estimationName
# writeStatsReports(netDataSavePath, netDataList)
# netDataSavePath = "./netData/" + traceName + "_netData" + "_" + estimationName
# writeStatsReports(netDataSavePath, netDataList)

#
# def hybirdEstimatorTest(tracePath, modelPath):
# 	estimationName = "GCC-RTS"
# 	dirNameDate = "result-" + estimationName + "/"
# 	env = GymEnv()
# 	env.init4Test(tracePath)
# 	trace = Trace(traceFilePath=tracePath)
# 	trace.readTraceFile()
# 	trace.preFilter()
# 	trace.filterForTime()
#
# 	traceName, tracePatterns = trace.traceName, trace.tracePatterns
#
# 	state_dim = 5
# 	model = ActorCritic(state_dim, 1, exploration_param=0.05)
# 	model.load_state_dict(torch.load(modelPath))
#
# 	max_step = 100000
# 	traceDone = False
#
# 	step = 0
# 	recvList = []
# 	stepList = []
# 	delayList = []
# 	lossList = []
# 	hatRate = []
# 	rate = env.lastBwe
# 	targetRate = []
# 	state = torch.Tensor([0.0 for _ in range(state_dim)])
#
# 	while not traceDone and step < max_step:
# 		action, _, _ = model.forward(state)
# 		rate, traceDone, recvRate, delay, qos3, qos4, state = env.stepHybird(action, step)
#
# 		targetRate.append(float(log_to_linear(action)))
# 		recvList.append(float(log_to_linear(state[0])))
#
# 		delayList.append(float(delay))
# 		lossList.append(float(state[2]))
# 		hatRate.append()
# 		state = torch.Tensor(state)
# 		stepList.append(step)
# 		step += 1
#
# 	dirName = "fig-rts"
#
# 	gccRate = genLineV2(stepList, [x / 1000 for x in targetRate], traceName + "-gccRate" + "-" + estimationName)
# 	recvRate = genLineV2(stepList, [x / 1000 for x in recvList], traceName + "-recvRate" + "-" + estimationName)
# 	delayCurve = genLineV2(stepList, delayList, traceName + "-delay-" + estimationName)
# 	lossCurve = genLineV2(stepList, lossList, traceName + "-loss-" + estimationName)
# 	hatRateCurve = genLineV2(stepList, hatRate, traceName + "-hatRate-" + estimationName)
# 	traceCap = trace.genLine("capacity", smooth=False)
# 	drawLine(dirName, dirNameDate, gccRate, recvRate, traceCap)
# 	drawLine(dirName, dirNameDate, delayCurve)
# 	drawLine(dirName, dirNameDate, lossCurve)
#
#
# def genLineV2(x, y, name, smooth=False) -> Line:
# 	tmp = Line()
# 	tmp.name = name
# 	tmp.x = x
# 	if smooth:
# 		y = savgol_filter(y, 21, 4, mode="nearest")
# 	tmp.y = y
# 	return tmp
#
#
# def prefilter(y):
# 	y1 = np.abs(y)
# 	mediaQ = np.median(y1)
# 	# last = 0
# 	for i, v in enumerate(y):
# 		if abs(v) > 10 * mediaQ:
# 			y[i] = 10 * mediaQ
# 	# last = y[i]
# 	return y


"""
使用仿真环境，运行拥塞控制算法，获得中间数据，和结果，以及图片。
"""


def ruleAlgo(trace_path, algo_name):
	algo_tag = 0
	if algo_name == "GCCNative":
		algo_tag = 0
	elif algo_name == "GCCGemini":
		algo_tag = 1
	elif algo_name == "RTSRuler":
		algo_tag = 2
	
	env = GymEnv()
	trace = env.init4Test(trace_path)
	env.report.init(algo_name, trace)
	
	done = False
	step = 0
	bwe = env.lastBwe
	while not done:
		if algo_tag == 0:
			bwe, done, _ = env.testGccNative(bwe)
		elif algo_tag == 1:
			bwe, done, _ = env.testGccGemini(bwe)
		else:
			pass
		step += 1
	# ========= report part
	env.report.draw_rate_fig()
	env.report.draw_delay_fig()
	env.report.draw_loss_fig()
	env.report.draw_threshold_fig()


def drlAlgo(trace_path, model_path):
	algo_name = "RTSDrl"
	env = GymEnv()
	trace = env.init4Test(trace_path)
	env.report.init(algo_name, trace)
	
	dim = 5
	model = ActorCritic(dim, 1, exploration_param=0.05)
	model.load_state_dict(torch.load(model_path))
	
	done = False
	step = 0
	# bwe = env.lastBwe
	state = torch.Tensor([0.0 for _ in range(dim)])
	while not done:
		action, _, _ = model.forward(state)
		state, done = env.testDrl(action)
		step += 1
		state = torch.Tensor(state)
	# ========= report part
	env.report.draw_rate_fig()
	env.report.draw_delay_fig()
	env.report.draw_loss_fig()


def hyAlgo(trace_path, model_path, algo_tag):
	pass


"""
tool function
"""

if __name__ == "__main__":
	pass

# traceFiles = glob.glob(f"./mytraces/ori_traces_preprocess/*.json", recursive=False)
# # traceFiles = glob.glob(f"./mytraces/special_trace/03.json", recursive=False)
#
# models = "./model/ppo_2021_05_13_01_55_53.pth"
# for ele in traceFiles:
# 	estimatorTest(ele, 0)
# for ele in traceFiles:
# 	estimatorTest(ele, 1)
# for ele in traceFiles:
# # 	estimatorTest(ele, 1)
# for ele in traceFiles:
# 	drlEstimatorTest(ele, models)
# for ele in traceFiles:
# 	hybirdEstimatorTest(ele, models)
