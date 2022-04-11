import csv
import os.path

import matplotlib.pyplot as plt


class Line:
	def __init__(self):
		self.name = None
		self.attrName = None
		self.x = []
		self.y = []


def drawLine(dirName, bigName, *data: Line):
	if not os.path.exists(dirName):
		os.mkdir(dirName)
	bigName = bigName
	for line in data:
		x = line.x  #
		y = line.y  # 
		name = line.name
		plt.plot(x, y, label=name)
	plt.legend()
	plt.savefig(dirName + "/" + bigName)
	plt.show()
	plt.close()


def drawWith15Scale(bigName, *data: Line):
	bigName = bigName
	for line in data:
		# x = line.x  # report_interval
		y = line.y
		y = [sum(x) / len(x) for x in chunked(y, 15)]
		name = line.name
		plt.plot(y, label=name)
	plt.legend()
	plt.savefig("./fig/test" + bigName)
	plt.show()
	plt.close()


def read_original_csv(path) -> dict:
	"""
	# 0:receiving_rate 1: delay 2: loss_ratio 3: delta_time 4:gcc_target_rate
	"""
	recv_rate = []
	delay = []
	loss = []
	deltaTime = []
	absTime = []
	target_rate = []
	with open(path, "r", encoding="utf-8") as f:
		reader = csv.reader(f)
		n = 0
		for row in reader:
			if n == 0:
				n += 1
				continue
			recv_rate.append(float(row[1]))
			delay.append(float(row[2]))
			loss.append(float(row[3]))
			if len(absTime) == 0:
				absTime.append(float(row[4]))
				continue
			tmp = absTime[-1] + float(row[3])
			absTime.append(tmp)
			target_rate.append(row[5])
	
	stat = {"recv_rate": recv_rate, "delay": delay, "loss": loss, "time": absTime, "target_rate": target_rate}
	return stat


def genLine(index, stat) -> Line:
	l = Line()
	l.name = index
	l.x = stat["time"]
	l.y = stat[index]
	return l


if __name__ == '__main__':
	gccFile_4g = "record_state_4G_3mbps.csv"
	gcc_4g = read_original_csv(gccFile_4g)
	recvRate = genLine("recv_rate", gcc_4g)
	delay = genLine("delay", gcc_4g)
	targetRate = genLine("target_rate", gcc_4g)
