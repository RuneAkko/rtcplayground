from utils.info import pktInfo


class pktGroup:
	def __init__(self):
		self.pkts = []
		
		self.arrivalTs = 0  # 该组最后包的到达时刻
		self.sendTs = 0  # 该组最后包的发送时刻
		
		self.rtt = 0  # 该组最后包的 rtt
		self.size = 0
	
	def addPkt(self, pkt: pktInfo):
		self.pkts.append(pkt)
		
		self.arrivalTs = pkt.receive_timestamp_ms
		self.sendTs = pkt.send_timestamp_ms
		self.rtt = pkt.rtt
		self.size += pkt.size
