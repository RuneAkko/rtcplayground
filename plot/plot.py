import csv

import matplotlib.pyplot as plt
import numpy as np


def draw(a, b, name):
	# a is e-gcc, b is gcc
	
	drawDelay([a["time"], a["delay"]], [b["time"], b["delay"]], name)
	
	drawLoss([a["time"], a["loss"]], [b["time"], b["loss"]], name)
	drawRate([a["time"], a["rate"]], [b["time"], b["rate"]], name)


def drawDelay(a, b, name):
	a = a[1]
	b = b[1]
	print("##############{} delay stats##########\n".format(name))
	print("mean delay   e-gcc:{},gcc:{}".format(np.mean(a), np.mean(b)))
	print("var delay   e-gcc:{},gcc:{}".format(np.var(a), np.var(b)))
	print("medium delay   e-gcc:{},gcc:{}".format(np.median(a), np.median(b)))
	# ax = a[0]
	# at = ax[0]
	# bx = b[0]
	# bt = bx[0]
	# ax = [i - at for i in ax]
	# bx = [i - bt for i in bx]
	# plt.plot(ax, a[1], label='e-gcc')
	# plt.plot(bx, b[1], label='gcc')
	plt.plot(a, label='e-gcc')
	plt.plot(b, label='gcc')
	plt.xlabel("interval")
	plt.ylabel("delay(ms)")
	plt.title(name)
	plt.legend()
	# plt.show()
	plt.savefig("delay.jpg")
	plt.close()


def drawLoss(a, b, name):
	a = a[1]
	b = b[1]
	print("##############{} loss stats##########\n".format(name))
	print("mean loss   e-gcc:{},gcc:{}".format(np.mean(a), np.mean(b)))
	print("var loss   e-gcc:{},gcc:{}".format(np.var(a), np.var(b)))
	print("medium loss   e-gcc:{},gcc:{}".format(np.median(a), np.median(b)))
	# ax = a[0]
	# at = ax[0]
	# bx = b[0]
	# bt = bx[0]
	# ax = [i - at for i in ax]
	# bx = [i - bt for i in bx]
	# plt.plot(ax, a[1], label='e-gcc')
	# plt.plot(bx, b[1], label='gcc')
	plt.plot(a, label='e-gcc')
	plt.plot(b, label='gcc')
	plt.xlabel("interval")
	plt.ylabel("loss")
	plt.title(name)
	plt.legend()
	# plt.show()
	plt.savefig("loss.jpg")
	plt.close()


def drawRate(a, b, name):
	a = a[1]
	b = b[1]
	print("##############{} rate stats##########\n".format(name))
	print("mean rate   e-gcc:{},gcc:{}".format(np.mean(a), np.mean(b)))
	print("var rate   e-gcc:{},gcc:{}".format(np.var(a), np.var(b)))
	print("medium rate   e-gcc:{},gcc:{}".format(np.median(a), np.median(b)))
	# ax = a[0]
	# at = ax[0]
	# bx = b[0]
	# bt = bx[0]
	# ax = [i - at for i in ax]
	# bx = [i - bt for i in bx]
	# plt.plot(ax, a[1], label='e-gcc')
	# plt.plot(bx, b[1], label='gcc')
	plt.plot(a, label='e-gcc')
	plt.plot(b, label='gcc')
	plt.xlabel("interval")
	plt.ylabel("rate(mbps)")
	plt.title(name)
	plt.legend()
	# plt.show()
	plt.savefig("rate.jpg")
	plt.close()


def read_original_csv(path):
	"""
	# 0:receiving_rate 1: delay 2: loss_ratio 3: delta_time
	
	:param path:
	:return:
	"""
	rate = []
	delay = []
	loss = []
	deltaTime = []
	absTime = []
	with open(path, "r", encoding="utf-8") as f:
		reader = csv.reader(f)
		n = 0
		for row in reader:
			if n == 0:
				n += 1
				continue
			rate.append(float(row[1]))
			delay.append(float(row[2]))
			loss.append(float(row[3]))
			if len(absTime) == 0:
				absTime.append(float(row[4]))
				continue
			tmp = absTime[-1] + float(row[3])
			absTime.append(tmp)
	
	stat = {"rate": rate, "delay": delay, "loss": loss, "time": absTime}
	return stat


if __name__ == '__main__':
	# case 1
	# 4g-3mbps
	#
	file = "/Users/hansenma/mhspion/preTest/GCCmix/"
	eGccFile_4g = file + "record_state_new_version2_4G_3mbps_2_trace_for_enhanceGCC.csv"
	eGCC_4g = read_original_csv(eGccFile_4g)
	gccFile_4g = file + "record_state_new_version2_4G_3mbps_2_trace_for_pureGCC.csv"
	gcc_4g = read_original_csv(gccFile_4g)
	
	draw(eGCC_4g, gcc_4g, "4G-3mbps")
