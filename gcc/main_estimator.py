from utils.info import pktInfo
from utils.my_enum import interfaceState
from utils.record import pktRecord
from .gcc_twcc_estimator import GCC

BaseDelay = 200  # ms, 假设传播时延


class GccNativeEstimator(object):
	def __init__(self, initialBwe, maxBwe, minBwe, filterType):
		self.pktsRecord = pktRecord(BaseDelay)
		self.pktsRecord.reset()
		
		self.state = interfaceState.INIT
		
		self.gcc = GCC(initialBwe, filterType)
		
		# last interval value or initial value, bps, int
		self.predictionBandwidth = initialBwe
		
		self.minBwe = minBwe
		self.maxBwe = maxBwe
		
		self.stats = []
	
	def report_states(self, stats: dict):
		"""
		stats is a rtp pkt to a dict with the following items
		{
			"send_time_ms": uint,
			"arrival_time_ms": uint,
			"payload_type": int,
			"sequence_number": uint,
			"ssrc": int,
			"padding_length": uint,
			"header_length": uint,
			"payload_size": uint
		},
		example:
		[
			{
				'arrival_time_ms': 66113,
				'header_length': 24,
				'padding_length': 0,
				'payload_size': 1389,
				'payload_type': 126,
				'send_time_ms': 60999,
				'sequence_number': 54366,
				'ssrc': 12648429
			},
			{
				'arrival_time_ms': 66181,
				'header_length': 24,
				'padding_length': 0,
				'payload_size': 1389,
				'payload_type': 126,
				'send_time_ms': 61069,
				'sequence_number': 54411,
				'ssrc': 12648429}
		]
		"""
		if self.state == interfaceState.ESTIMATE:
			self.stats = []
		self.state = interfaceState.REPORT
		
		if len(stats) <= 0:
			return
		
		pkt_info = pktInfo()
		pkt_info.payload_type = stats["payload_type"]
		pkt_info.ssrc = stats["ssrc"]
		pkt_info.sequence_number = stats["sequence_number"]
		pkt_info.send_timestamp_ms = stats["send_time_ms"]
		pkt_info.receive_timestamp_ms = stats["arrival_time_ms"]
		pkt_info.padding_length = stats["padding_length"]
		pkt_info.header_length = stats["header_length"]
		pkt_info.payload_size = stats["payload_size"]
		
		pkt_info.size = stats["padding_length"] + \
		                stats["header_length"] + stats["payload_size"]
		
		pkt_info.bandwidth_prediction_bps = self.predictionBandwidth
		
		# todo: 确认是否应该给包加上假设的 base delay
		self.pktsRecord.on_receive(pkt_info)
		
		self.gcc.rateCalculator.update(pkt_info)
		
		self.gcc.rttCalculator.simpleRtt(self.pktsRecord.pkts[-1].delay)
		
		self.gcc.currentTimestamp = pkt_info.receive_timestamp_ms
		
		self.stats.append(stats)
	
	def get_estimated_bandwidth(self) -> int:
		if self.state == interfaceState.REPORT:
			self.state = interfaceState.ESTIMATE
		# else:
		# 	return self.predictionBandwidth
		
		assert self.pktsRecord.packet_num > 0
		
		self.gcc.setIntervalState(self.pktsRecord, self.stats)
		
		self.predictionBandwidth = self.gcc.getEstimateBandwidth()
		
		return self.predictionBandwidth
