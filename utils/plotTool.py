import csv
import os.path
import json
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter


class Line:
	def __init__(self):
		self.name = None
		self.attrName = None
		self.x = []
		self.y = []
		self.y_label = None


def drawLineV2(dirName, fileName, *data: Line, smooth=False, ):
	"""
	画单个算法的表现
	:param dirName:
	:param data:
	:return:
	"""
	if not os.path.exists(dirName):
		os.mkdir(dirName)
	
	for line in data:
		# x = line.x  #
		# x time axis, default interval-60ms
		# turn to second
		# x = [tmp * 60 / 1000 for tmp in line.x]
		x = line.x
		y = line.y  #
		linename = line.name
		if linename == "link capacity":
			line_color = '#FA7F6F'
			line_shape = '-'
			plt.plot(x, y, line_shape, color=line_color, label=linename)
		elif linename == "estimate bandwidth":
			line_color = '#FFBE7A'
			line_shape = '-'
			if smooth:
				y = savgol_filter(y, 21, 1, mode="nearest")
			plt.plot(x, y, line_shape, color=line_color, label=linename)
		elif linename == "recv rate":
			line_color = '#8ECFC9'
			line_shape = '--'
			if smooth:
				y = savgol_filter(y, 11, 4, mode="nearest")
			plt.plot(x, y, line_shape, color=line_color, label=linename)
		elif linename == "threshold(gamma)":
			line_color = '#FA7F6F'
			line_shape = '--'
			plt.plot(x, y, line_shape, color=line_color, label=linename)
			plt.plot(x, [-1 * t for t in y], line_shape, color=line_color)
		else:
			line_color = '#82B0D2'
			line_shape = '-'
			plt.plot(x, y, line_shape, color=line_color, label=linename)
	
	# plt.ylabel(data[0].y_label)
	plt.xlabel("time(second)")
	plt.legend()
	plt.savefig(dirName + "/" + fileName)
	plt.close()


def drawLine(dirName, dirData, x_label, y_label, *data: Line):
	if not os.path.exists(dirName):
		os.mkdir(dirName)
	if not os.path.exists(dirData):
		os.mkdir(dirData)
	
	bigName = data[0].name
	for line in data:
		# x = line.x  #
		# x time axis, default interval-60ms
		# turn to second
		x = [tmp * 60 / 1000 for tmp in line.x]
		y = line.y  # 
		name = line.name
		
		with open(dirData + "/" + line.name + "-yaxis", "w") as f:
			f.write(json.dumps(y))
		
		with open(dirData + "/" + line.name + "-xaxis", "w") as f:
			f.write(json.dumps(x))
		
		# name = name.split("-")[]
		
		plt.plot(x, y, label=name)
	
	plt.xlabel(x_label)
	plt.ylabel(y_label)
	plt.legend()
	plt.savefig(dirName + "/" + bigName)
	plt.show()
	plt.close()


def drawScatter(dirName, *data: Line):
	if not os.path.exists(dirName):
		os.mkdir(dirName)
	bigName = data[0].name
	for line in data:
		# x = line.x  #
		# x time axis, default interval-60ms
		# turn to second
		x = [tmp * 60 / 1000 for tmp in line.x]
		y = line.y  #
		name = line.name
		plt.scatter(x, y, label=name)
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
