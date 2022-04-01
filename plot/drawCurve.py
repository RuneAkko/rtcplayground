import matplotlib.pyplot as plt


class Line:
	def __init__(self):
		self.name = None
		self.x = []
		self.y = []


def draw(*data: Line):
	for line in data:
		x = line.x
		y = line.y
		name = line.name
		plt.plot(x, y, label=name)
		plt.savefig("test"+line.name)
		plt.show()
		
		plt.close()
