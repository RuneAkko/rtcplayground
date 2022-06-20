import glob
import json

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
from scipy.interpolate import griddata
from utils.multi_verus import draw_cdf_fig, cal_mean_qos
import copy
from utils.my_enum import ccAlgo, traceSetType
from random import sample
from utils.qosReport import Curve, Figure

"""
使用仿真环境，运行拥塞控制算法，获得中间数据，和结果，以及图片。
"""


def adaptiveThresholdTurning():
	algo_name = ccAlgo.HRCC_KAL.value
	
	# trace_path = "./mytraces/special_trace_preprocess/stable-var-link-short.json"
	trace_path = "./mytraces/ori_traces_preprocess/4G_3mbps.json"
	k_up_list = []
	k_down_list = []
	start = 0.001
	end = 0.05
	tmp = start
	while tmp <= end:
		k_up_list.append(tmp)
		k_down_list.append(tmp)
		tmp += 0.005
	x, y, z = [], [], []
	points = []
	step = 0
	records = []
	for k_up in k_up_list:
		for k_down in k_down_list:
			env = GymEnv(k_up=k_up, k_down=k_down)
			trace = env.init4Test(trace_path)
			env.report.init(algo_name, trace)
			done = False
			bwe = env.lastBwe
			while not done:
				bwe, done, _ = env.testHrccGccWithKal(bwe)
			step += 1
			x.append(k_up)
			y.append(k_down)
			points.append(([k_up, k_down]))
			env.report.calculateQos()
			env.report.calculateU()
			print(env.report.object_U)
			z.append(env.report.object_U)
			records.append({
				"x": k_up,
				"y": k_down,
				"z": z
			})
	
	# env.report.draw_delay_fig()
	points = np.array(points)
	x, y = np.meshgrid(x, y)
	zi = griddata(points, z, (x, y))
	c = plt.contour(x, y, zi, 5)
	plt.xlabel("k_up")
	plt.ylabel("k_down")
	plt.clabel(c, inline=True, fontsize=8)
	plt.colorbar()
	plt.savefig("test")
	
	with open("optimal", "w") as f:
		f.write("begin\n")
		for ele in records:
			tmp = json.dumps(ele)
			f.write(tmp + "\n")


def draw_cdf_main(trace_path, algo_names):
	reports = []
	for algo_name in algo_names:
		if algo_name == ccAlgo.RTSDRL:
			model_2 = "./model/ppo_2021_07.pth"  # best
			reports.append(drlAlgo(trace_path, model_2, ""))
		elif algo_name == ccAlgo.RTSHY:
			model_2 = "./model/ppo_2021_07.pth"
			reports.append(hyAlgo(trace_path, model_2, ""))
		else:
			reports.append(ruleAlgo(trace_path, algo_name))
	draw_cdf_fig(reports, "_".join([x.value for x in algo_names]))


def draw_cdf_main_real(trace_paths, algo_name):
	reports = []
	for trace_path in trace_paths:
		if algo_name == ccAlgo.RTSDRL:
			model_2 = "./model/ppo_2021_07.pth"  # best
			reports.append(drlAlgo(trace_path, model_2, "", isSave=False))
		elif algo_name == ccAlgo.RTSHY:
			model_2 = "./model/ppo_2021_07.pth"
			reports.append(hyAlgo(trace_path, model_2, "", isSave=False))
		else:
			reports.append(ruleAlgo(trace_path, algo_name, isSave=False))
	
	save_file = "./result/real/qos_result"
	
	sum_list = []
	
	for ele in reports:
		sum_list = np.sum([sum_list,
		                   [ele.util, ele.d_aver, ele.d_50, ele.d_95, ele.l_aver, ele.qos_u, ele.qos_d, ele.qos_l,
		                    ele.qos]], axis=0)
	
	mean_list = [round(x / len(trace_paths), 2) for x in sum_list]
	
	print("=" * 4)
	res_list = [str(x) for x in mean_list]
	res = algo_name.value + " & " + " & ".join(res_list) + " \\\\ "
	print(res)


# draw_cdf_fig(reports, "_".join([x.value for x in algo_names]))


def draw_cdf_main_drls(trace_path, model_names):
	reports = []
	model_path = ""
	for model in model_names:
		if model == "DRL05":
			model_path = "./model/ppo_2021_05.pth"
		elif model == "DRL07":
			model_path = "./model/ppo_2021_07.pth"
		elif model == "DRL04":
			model_path = "./model/ppo_2022_04_10_04_53_52.pth"
		else:
			pass
		reports.append(drlAlgo(trace_path, model_path, model))
	draw_cdf_fig(reports, "_".join(model_names))


def ruleAlgo(trace_path, algo_name, isSave=True):
	algo_tag = 0
	if algo_name == ccAlgo.GCC:  #
		algo_tag = 0
	elif algo_name == ccAlgo.GEMINI:  # trendline + magic
		algo_tag = 1
	elif algo_name == ccAlgo.RTSRule:
		algo_tag = 2
	elif algo_name == ccAlgo.HRCC:  # trendline
		algo_tag = 3
	elif algo_name == ccAlgo.HRCC_KAL:  # kalman
		algo_tag = 4
	else:
		pass
	env = GymEnv()
	trace = env.init4Test(trace_path)
	env.report.init(algo_name.value, trace, isSave)
	
	done = False
	step = 0
	bwe = env.lastBwe
	while not done:
		if algo_tag == 0:
			bwe, done, _ = env.testGccNative(bwe)
		elif algo_tag == 1:
			bwe, done, _ = env.testGccGemini(bwe)
		elif algo_tag == 3:
			bwe, done, _ = env.testHrccGcc(bwe)
		elif algo_tag == 4:
			bwe, done, _ = env.testHrccGccWithKal(bwe)
		else:
			pass
		step += 1
	env.report.calculateQos()
	# ========= report part
	if not isSave:
		report = copy.deepcopy(env.report)
		return report
	env.report.draw_rate_fig()
	env.report.draw_delay_fig()
	env.report.draw_loss_fig()
	env.report.draw_threshold_fig()
	env.report.printResult()
	report = copy.deepcopy(env.report)
	return report


def drlAlgo(trace_path, model_path, model_tag, isSave=True):
	algo_name = ccAlgo.RTSDRL.value + model_tag
	env = GymEnv()
	trace = env.init4Test(trace_path)
	env.report.init(algo_name, trace, isSave)
	
	dim = 5
	model = ActorCritic(dim, 1, exploration_param=0.05)
	model.load_state_dict(torch.load(model_path))
	
	done = False
	step = 0
	state = torch.Tensor([0.0 for _ in range(dim)])
	while not done:
		action, _, _ = model.forward(state)
		state, done = env.testDrl(action)
		step += 1
		state = torch.Tensor(state)
	env.report.calculateQos()
	# ========= report part
	if not isSave:
		report = copy.deepcopy(env.report)
		return report
	env.report.draw_rate_fig()
	env.report.draw_delay_fig()
	env.report.draw_loss_fig()
	env.report.printResult()
	report = copy.deepcopy(env.report)
	return report


def hyAlgo(trace_path, model_path, algo_tag, isSave=True):
	algo_name = ccAlgo.RTSHY.value
	env = GymEnv()
	trace = env.init4Test(trace_path)
	env.report.init(algo_name, trace, isSave)
	
	dim = 5
	model = ActorCritic(dim, 1, exploration_param=0.05)
	model.load_state_dict(torch.load(model_path))
	
	done = False
	state = torch.Tensor([0.0 for _ in range(dim)])
	while not done:
		action, _, _ = model.forward(state)
		state, done = env.testHy(action)
		state = torch.Tensor(state)
	env.report.calculateQos()
	# ========= report part
	if not isSave:
		report = copy.deepcopy(env.report)
		return report
	env.report.draw_rate_fig()
	env.report.draw_delay_fig()
	env.report.draw_loss_fig()
	env.report.printResult()
	report = copy.deepcopy(env.report)
	return report


"""
tool function
"""


def main_1():
	# path = f"./mytraces/special_trace_preprocess/stable-var-link.json"
	path = f"./mytraces/ori_traces_preprocess/WIRED_200kbps.json"
	model1 = "./model/ppo_2021_05.pth"
	model2 = "./model/ppo_2021_07.pth"
	model3 = "./model/ppo_2022_04_10_04_53_52.pth"
	traceFiles = glob.glob(path, recursive=False)
	for ele in traceFiles:
		# ruleAlgo(ele, ccAlgo.HRCC)
		ruleAlgo(ele, ccAlgo.GCC)


# ruleAlgo(ele, ccAlgo.HRCC_KAL)
# ruleAlgo(ele, ccAlgo.RTSHY)
# ruleAlgo(ele, ccAlgo.RTSDRL)
# ruleAlgo(ele, ccAlgo.GEMINI)


# draw_cdf_main(ele, [ccAlgo.GCC, ccAlgo.HRCC, ccAlgo.RTSDRL, ccAlgo.RTSHY])


# drlAlgo(ele, model1, "05")
# drlAlgo(ele, model2, "07")
# drlAlgo(ele, model3, "04")
# draw_cdf_main(ele, [ccAlgo.RTSHY])

# draw_cdf_main(ele, ["GCCNative", "GCCGemini", "GCCHrcc", "RTSDrl", "RTSHybrid"])
# draw_cdf_main(ele, [ccAlgo.GCC, ccAlgo.HRCC, ccAlgo.RTSDRL, ccAlgo.RTSHY, ccAlgo.GEMINI])


# draw_cdf_main_drls(ele, ["DRL05", "DRL07", "DRL04"])
# hyAlgo(ele, model2, "")

def main_2():
	path = "./mytraces/realtrace/preprocess/"
	files = ["2.json", "11.json", "45.json", "9.json"]
	files = ["9.json"]
	for ele in files:
		trace = path + ele
		ruleAlgo(trace, ccAlgo.HRCC)


# ruleAlgo(trace, ccAlgo.GCC)
# ruleAlgo(trace, ccAlgo.HRCC_KAL)
# ruleAlgo(trace, ccAlgo.RTSHY)
# ruleAlgo(trace, ccAlgo.RTSDRL)
# ruleAlgo(trace, ccAlgo.GEMINI)


# draw_cdf_main(trace, [ccAlgo.RTSHY])
# draw_cdf_main(trace, ["GCCNative", "GCCGemini", "GCCHrcc", "RTSHybird"])
# draw_cdf_main(trace, [ccAlgo.GEMINI, ccAlgo.HRCC, ccAlgo.RTSDRL, ccAlgo.RTSHY])


def main_3():
	# cal_mean_qos([ccAlgo.GCC, ccAlgo.HRCC, ccAlgo.RTSDRL, ccAlgo.RTSHY], traceSetType.WIRED)
	print("+" * 50)
	cal_mean_qos([ccAlgo.GCC, ccAlgo.HRCC, ccAlgo.RTSDRL, ccAlgo.RTSHY], traceSetType.LTE)


def main_4():
	"""
	real trace
	:return:
	"""
	path = f"./mytraces/realtrace/preprocess/*.json"
	traceFiles = glob.glob(path, recursive=False)
	# traceFiles = ["./mytraces/realtrace/preprocess/0.json", "./mytraces/realtrace/preprocess/1.json"]
	algos = [ccAlgo.GEMINI, ccAlgo.HRCC, ccAlgo.RTSDRL, ccAlgo.RTSHY]
	traceFiles = sample(traceFiles, 10)
	for ele in algos:
		draw_cdf_main_real(traceFiles, ele)


def main_5():
	"""
	special fig:
	绘制两种时延梯度估计方案的估计结果，并与真实时延变化量比较
	:return:
	"""
	path = f"./mytraces/special_trace_preprocess/*.json"
	traceFiles = glob.glob(path, recursive=False)
	save_path = "./result/vs1/"
	for ele in traceFiles:
		r = ruleAlgo(ele, ccAlgo.HRCC, isSave=False)
		trend = r.queueDelayDelta
		trend_real = r.queueDelayDelta_m
		r = ruleAlgo(ele, ccAlgo.HRCC_KAL, isSave=False)
		kal = r.queueDelayDelta
		kal_real = r.queueDelayDelta_m
		
		t_1 = Curve({
			"name": "estimate",
			"color": "#82B0D2",  # blue
			"shape": "-"
		})
		t_1.update(trend)
		t_2 = Curve({
			"name": "reality",
			"color": "#FA7F6F",  # blue
			"shape": "-"
		})
		t_2.update(trend_real)
		f_1 = Figure({
			"x-label": "time(second)",
			"y-label": "queue delay gradient",
			"dir": save_path + r.trace_name + "/trend/",
			"file": "qdg"
		}, [t_1, t_2])
		f_1.save()
		k_1 = Curve({
			"name": "estimate",
			"color": "#82B0D2",  # blue
			"shape": "-"
		})
		k_1.update(kal)
		k_2 = Curve({
			"name": "reality",
			"color": "#FA7F6F",  # blue
			"shape": "-"
		})
		k_2.update(kal_real)
		f_2 = Figure({
			"x-label": "time(second)",
			"y-label": "queue delay gradient",
			"dir": save_path + r.trace_name + "/kal/",
			"file": "qdg"
		}, [k_1, k_2])
		f_2.save()


if __name__ == "__main__":
	main_1()
# main_2()
# main_3()
# main_4()
# main_5()
# adaptiveThresholdTurning()
