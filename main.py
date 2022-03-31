from plot.drawCurve import Line
from plot.drawCurve import draw
from rtc_env import GymEnv
from utils.trace_analyse import getTrace


def ruleEstimatorTest(path):
	"""
	
	:return:
	"""
	env = GymEnv()
	name, _ = getTrace(path)
	env.set(path)
	
	max_step = 1000
	traceDone = None
	step = 0
	qosList = []
	stepList = [step]
	
	rate = env.ruleEstimator.predictionBandwidth
	targetRate = [rate]
	
	while not traceDone and step < max_step:
		rate, traceDone, qos = env.test(rate)
		qosList.append(qos)
		step += 1
		stepList.append(step)
		targetRate.append(rate)
	
	# realRate = Line()
	# realRate.name = "cap"
	gccRate = Line()
	gccRate.name = "targetRate"
	gccRate.x = stepList
	gccRate.y = targetRate
	
	draw(gccRate)


if __name__ == "__main__":
	testTracePath = "./traces/4G_500kbps.json"
	ruleEstimatorTest(testTracePath)
