import json
import logging
import os.path
import time

from scipy.signal import savgol_filter

from gcc.main_estimator import GccNativeEstimator
from geminiGCC.main_estimator import GccGeminiEstimator
from utils.plotTool import drawLine, Line
from utils.utilBackup.packet_info import PacketInfo
from utils.utilBackup.packet_record import PacketRecord
from utils.trace import Trace


def writeStatsReports(file, data):
	# if not os.path.exists(path):
	# 	os.mkdir(path)
	with open(file, "w") as f:
		f.write("begin\n")
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


def get_time_ms():
	return int(time.time() * 1000)


INIT_BANDWIDTH = 3000 * 1000  # 3m bps


class testEnv:
	def __init__(self, netData):
		self.step_time = 60  # ms
		self.estimator = None
		self.lastEstimationTs = 0
		self.testReports = netData
		self.tag = -1
		self.lastBwe = INIT_BANDWIDTH
		self.packet_record = PacketRecord()
	
	def setTestEnv(self, tag):
		self.tag = tag
		if tag == 0:
			self.estimator = GccNativeEstimator(INIT_BANDWIDTH)
		else:
			self.estimator = GccGeminiEstimator(INIT_BANDWIDTH)
	
	def test(self, targetRate, stepNum):
		
		if self.tag == 0:
			return self.testV1(targetRate, stepNum)
		else:
			return self.testV2(targetRate, stepNum)
	
	def testV1(self, targetRate, stepNum):
		for pkt in self.testReports[stepNum]:
			self.estimator.report_states(pkt)
		
		targetRate = self.lastBwe
		
		if len(self.testReports[stepNum]) > 2:
			nowTs = self.estimator.gcc.currentTimestamp
			if (nowTs - self.lastEstimationTs) >= 200:
				self.lastEstimationTs = nowTs
			logging.info("now time :[%s]", nowTs)
			targetRate = self.estimator.get_estimated_bandwidth()
		
		if targetRate != 0:
			self.lastBwe = targetRate
		
		recvRate, delay, _, _ = self.calculateNetQos()
		logging.info("average delay [%s]", delay)
		logging.info("recv rate [%s]mbps", recvRate / 1000000)
		return self.lastBwe, recvRate
	
	def testV2(self, targetRate, stepNum):
		pkt_list = self.testReports[stepNum]
		if len(pkt_list) < 2:
			return self.lastBwe, 0
		
		next_targetRate = self.lastBwe
		if len(pkt_list) > 0:
			now_ts = get_time_ms() - self.estimator.first_time
			logging.info("now time : [%s]", now_ts)
			self.estimator.gcc_ack_bitrate.ack_estimator_incoming(pkt_list)
			result = self.estimator.gcc_rate_controller.delay_bwe_incoming(
				pkt_list, self.estimator.gcc_ack_bitrate.ack_estimator_bitrate_bps(),
				now_ts)
			next_targetRate = result.bitrate
		
		if next_targetRate != 0:
			self.lastBwe = next_targetRate
		
		# if len(pkt_list) > 0:
		for pkt in pkt_list:
			if len(pkt) <= 0:
				continue
			packet_info = PacketInfo()
			packet_info.payload_type = pkt["payload_type"]
			packet_info.ssrc = pkt["ssrc"]
			packet_info.sequence_number = pkt["sequence_number"]
			packet_info.send_timestamp = pkt["send_time_ms"]
			packet_info.receive_timestamp = pkt["arrival_time_ms"]
			packet_info.padding_length = pkt["padding_length"]
			packet_info.header_length = pkt["header_length"]
			packet_info.payload_size = pkt["payload_size"]
			packet_info.bandwidth_prediction = self.lastBwe
			self.packet_record.on_receive(packet_info)
		qos1, qos2, qos3, qos4 = self.calculateNetQosV2()
		logging.info("average delay [%s]", qos2)
		logging.info("target rate [%s] mbps", self.lastBwe / 1000000)
		logging.info("recv rate [%s]mbps", qos1 / 1000000)
		return self.lastBwe, qos1
	
	def calculateNetQos(self):
		recv_rate = self.estimator.pktsRecord.calculate_receiving_rate(
			interval=self.step_time)
		delay = self.estimator.pktsRecord.calculate_average_delay(
			interval=self.step_time)
		loss = self.estimator.pktsRecord.calculate_loss_ratio(
			interval=self.step_time)
		gccBwe = self.estimator.pktsRecord.calculate_latest_prediction()
		return recv_rate, delay, loss, gccBwe
	
	def calculateNetQosV2(self):
		recv_rate = self.packet_record.calculate_receiving_rate(
			interval=self.step_time)
		delay = self.packet_record.calculate_average_delay(
			interval=self.step_time)
		loss = self.packet_record.calculate_loss_ratio(
			interval=self.step_time)
		lastGccBwe = self.packet_record.calculate_latest_prediction()
		return recv_rate, delay, loss, lastGccBwe


if __name__ == "__main__":
	
	tag = 1
	
	tracePath = "./mytraces/new_version2_4G_3mbps_2_trace.json"
	if tag == 0:
		netDataPath = "./netData/new_version2_4G_3mbps_2_trace_netData_OwnGCC"
	else:
		netDataPath = "./netData/new_version2_4G_3mbps_2_trace_netData_GeminiGCC"
	
	logName = "test" + str(tag) + ".log"
	
	if os.path.exists(logName):
		os.remove(logName)
	
	LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
	DATE_FORMAT = "%m/%d/%Y %H:%M:%S %p"
	logging.basicConfig(filename=logName, level=logging.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT)
	
	reports = readStatsReports(netDataPath)
	
	step = 0
	stepList = [step]
	maxStep = len(reports)
	env = testEnv(reports)
	env.setTestEnv(tag)
	gccRate = env.lastBwe
	rates = [gccRate]
	recvRates = [0]
	while step < maxStep:
		gccRate, recvRate = env.test(gccRate, step)
		rates.append(gccRate)
		recvRates.append(recvRate)
		step += 1
		stepList.append(step)
	
	name = "LocalTest" + "v" + str(tag)
	gccRateFig = Line()
	gccRateFig.name = name + "-targetRate"
	gccRateFig.x = stepList
	gccRateFig.y = [x / 1000000 for x in rates]
	gccRateFig.y = savgol_filter(gccRateFig.y, 20, 1, mode="nearest")
	
	recvRateFig = Line()
	recvRateFig.name = name + "-recvRate"
	recvRateFig.x = stepList
	recvRateFig.y = [x / 1000000 for x in recvRates]
	recvRateFig.y = savgol_filter(recvRateFig.y, 20, 1, mode="nearest")
	
	trace = Trace(traceFilePath=tracePath)
	trace.readTraceFile()
	trace.preFilter()
	traceCap = trace.genLine("capacity", smooth=True)
	
	drawLine("localtest", name, gccRateFig, recvRateFig, traceCap)
