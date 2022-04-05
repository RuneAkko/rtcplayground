from utils.my_enum import Signal

from utils.my_enum import State


class StateMachine:
	def __init__(self):
		self.pre_state = State.HOLD
		self.pre_signal = Signal.NORMAL
	
	def transition(self, signal: Signal) -> State:
		if signal == Signal.OVER_USE and self.pre_state == State.HOLD:
			self.pre_state = State.DECREASE
		if signal == Signal.OVER_USE and self.pre_state == State.INCREASE:
			self.pre_state = State.DECREASE
		if signal == Signal.OVER_USE and self.pre_state == State.DECREASE:
			self.pre_state = State.DECREASE
		
		if signal == Signal.NORMAL and self.pre_state == State.HOLD:
			self.pre_state = State.INCREASE
		if signal == Signal.NORMAL and self.pre_state == State.INCREASE:
			self.pre_state = State.INCREASE
		if signal == Signal.NORMAL and self.pre_state == State.DECREASE:
			self.pre_state = State.HOLD
		
		if signal == Signal.UNDER_USE and self.pre_state == State.HOLD:
			self.pre_state = State.HOLD
		if signal == Signal.UNDER_USE and self.pre_state == State.INCREASE:
			self.pre_state = State.HOLD
		if signal == Signal.UNDER_USE and self.pre_state == State.DECREASE:
			self.pre_state = State.HOLD
		
		return self.pre_state
