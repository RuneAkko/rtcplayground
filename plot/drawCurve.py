import matplotlib.pyplot as plt
from more_itertools import chunked


class Line:
	def __init__(self):
		self.name = None
		self.x = []
		self.y = []


def draw(bigName, *data: Line):
	bigName = bigName
	for line in data:
		# x = line.x  # report_interval
		y = line.y  # 
		name = line.name
		plt.plot(y, label=name)
	plt.legend()
	plt.savefig("./fig/test" + bigName)
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
