from utils.packetInfo import PacketInfo
from utils.packetRecord import PacketRecord


class Esitimator(object):
	def __init__(self):
		self.predictionBandwidth = None  # int, bps
		
		self.pktsRecord = PacketRecord(0)
		self.pktsRecord.reset()
		
		self.lastInvokeState = "init"
	
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
        }
        """
		if self.lastInvokeState == "get_estimated_bandwidth":
			self.pktsRecord.clear()
		self.lastInvokeState = "report_states"
		
		pktInfo = PacketInfo()
		pktInfo.payload_type = stats["payload_type"]
		pktInfo.ssrc = stats["ssrc"]
		pktInfo.sequence_number = stats["sequence_number"]
		pktInfo.send_timestamp = stats["send_time_ms"]
		pktInfo.receive_timestamp = stats["arrival_time_ms"]
		pktInfo.padding_length = stats["padding_length"]
		pktInfo.header_length = stats["header_length"]
		pktInfo.payload_size = stats["payload_size"]
		
		pktInfo.bandwidth_prediction = self.predictionBandwidth
		
		self.pktsRecord.on_receive(pktInfo)
	
	def get_estimated_bandwidth(self) -> int:
		if self.lastInvokeState and self.lastInvokeState == "report_states":
			self.lastInvokeState = "get_estimated_bandwidth"
		return self.predictionBandwidth
