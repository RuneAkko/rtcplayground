class unsafety_detector:  #
	def __init__(self, window_size=20):
		self.window_size = window_size
		self.index = 0
		self.arrival_delta_list = [0.0 for _ in range(self.window_size)]
		self.last_D = 1
		self.gamma = 1
		self.state = 1  # 1/0 1:DL;0:GCC
		self.k = 0.5
		
		self.change_window = 10  # 进行一次切换之后十次之后再改变
		
		self.last_recv = None
		self.last_send = None
		
		self.last_result = 0
	
	# # ## 用于测试
	# self.state=1
	# self.change_window=10
	# print("测试,state 恒定")
	def receive(self, recv, send):
		if self.last_recv == None:
			self.last_recv = recv
			self.last_send = send
		else:
			recv_delta_ms = recv - self.last_recv
			send_delta_ms = send - self.last_send
			self.update(recv_delta_ms, send_delta_ms)
			self.last_recv = recv
			self.last_send = send
	
	def update(self, recv_delta_ms, send_delta_ms, arrival_ts=0):
		
		delta_ms = recv_delta_ms - send_delta_ms
		
		# mean_delta=0
		if delta_ms > 0:
			self.index += 1
			self.last_D = self.last_D * 1 / 2 + delta_ms
			self.gamma = self.gamma + self.k * (self.last_D - self.gamma)
			# print(delta_ms)
			
			if self.state == 1:
				if self.last_D > self.gamma and self.last_result >= 0:
					self.change_window -= 1
					if self.change_window == 0:
						self.state = 0
			else:
				if self.last_D <= self.gamma and self.last_result <= 0:
					self.change_window -= 1
				elif self.last_D > self.gamma and self.last_result >= 0:
					self.change_window += 1
					self.change_window = min(10, self.change_window)
					if self.change_window == 0:
						self.state = 1
			
			if self.change_window == 0:
				self.change_window = 10
			# print("state",self.state)
			self.last_result = self.last_D - self.gamma
		
		# ## 用于测试
		# self.state=1
		# self.change_window=10
		# print("state",self.state)
		# if self.state==0:
		#     print(self.change_window)
		return self.state
	
	def reset(self):
		# self.window_size=window_size
		self.index = 0
		self.arrival_delta_list = [0.0 for _ in range(self.window_size)]
		self.last_D = 200
		self.gamma = 1
		self.state = 1  # 1/0 1:DL;0:GCC
		self.k = 0.5
		
		self.change_window = 10  # 进行一次切换之后十次之后再改变
		
		self.last_recv = None
		self.last_send = None
	
	def detect_big_delay(self):
		self.change_window = 10
		self.state = 0
# ## 用于测试
# self.state=1
# self.change_window=10