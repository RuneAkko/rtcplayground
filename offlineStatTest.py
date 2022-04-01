import json


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
					continue
				tmp = json.loads(ele)
			# print(tmp)


if __name__ == "__main__":
	l = [{
		'arrival_time_ms': 66113,
		'header_length': 24,
		'padding_length': 0,
		'payload_size': 1389,
		'payload_type': 126,
		'send_time_ms': 60999,
		'sequence_number': 54366,
		'ssrc': 12648429}, {
		'arrival_time_ms': 66181,
		'header_length': 24,
		'padding_length': 0,
		'payload_size': 1389,
		'payload_type': 126,
		'send_time_ms': 61069,
		'sequence_number': 54411,
		'ssrc': 12648429}]
	
	test_data = [l, l]
	writeStatsReports("test", test_data)
	readStatsReports("test")
