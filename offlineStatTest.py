import json
import logging
import os.path

from gcc.main_estimator import mainEstimator
from plot.drawCurve import draw, Line


def writeStatsReports(path, data):
	with open(path, "w") as f:
		for repost in data:
			for stats in repost:
				stat = json.dumps(stats)
				f.write(stat + "\t")
			f.write("\n")


def readStatsReports(path):
	stats_reports = []
	with open(path, "r") as f:
		for line in f.readlines():
			statsStr = line.strip("\n").split("\t")
			report = []
			for ele in statsStr:
				if len(ele) < 2:
					tmp = {}
				else:
					tmp = json.loads(ele)
				report.append(tmp)
			stats_reports.append(report)
	return stats_reports


class testEnv:
	def __init__(self, netData):
		self.step_time = 60  # ms
		self.estimator = mainEstimator()
		self.lastEstimationTs = 0
		self.testReports = netData
	
	def test(self, targetRate, stepNum):
		for pkt in self.testReports[stepNum]:
			self.estimator.report_states(pkt)
		
		targetRate = self.estimator.predictionBandwidth
		
		if len(self.testReports[stepNum]) > 2:
			nowTs = self.estimator.gcc.currentTimestamp
			if (nowTs - self.lastEstimationTs) >= 200:
				logging.info("nowTs is [%s], lastTs is [%s]", nowTs, self.lastEstimationTs)
				self.lastEstimationTs = nowTs
				targetRate = self.estimator.get_estimated_bandwidth()
		
		recvRate, _, _, _ = self.calculateNetQos()
		
		return targetRate, recvRate
	
	def calculateNetQos(self):
		recv_rate = self.estimator.pktsRecord.calculate_receiving_rate(
			interval=self.step_time)
		delay = self.estimator.pktsRecord.calculate_average_delay(
			interval=self.step_time)
		loss = self.estimator.pktsRecord.calculate_loss_ratio(
			interval=self.step_time)
		gccBwe = self.estimator.pktsRecord.calculate_latest_prediction()
		return recv_rate, delay, loss, gccBwe


if __name__ == "__main__":
	
	if os.path.exists("test.log"):
		os.remove("test.log")
	
	LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
	DATE_FORMAT = "%m/%d/%Y %H:%M:%S %p"
	logging.basicConfig(filename="test.log", level=logging.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT)
	
	netDataPath = "./netData/5G_12mbps_netData"
	reports = readStatsReports(netDataPath)
	
	step = 0
	stepList = [step]
	maxStep = len(reports)
	env = testEnv(reports)
	gccRate = env.estimator.predictionBandwidth
	rates = [gccRate]
	while step < maxStep:
		gccRate, _ = env.test(gccRate, step)
		rates.append(gccRate)
		step += 1
		stepList.append(step)
	
	name = "LocalTest"
	gccRateFig = Line()
	gccRateFig.name = name + "-targetRate"
	gccRateFig.x = stepList
	gccRateFig.y = [x / 1000000 for x in rates]
	
	draw(name, gccRateFig)
	
	with open(name + "-testGccRate", "w") as f:
		f.write(str(gccRateFig.y))
