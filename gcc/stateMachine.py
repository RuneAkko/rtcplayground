from utils.enumSignal import Signal
from utils.enumState import State


class StateMachine:
	def __init__(self):
		self.state = State.HOLD
	
	def transition(self, signal: Signal) -> State:
		if signal == Signal.OVER_USE and self.state == State.HOLD:
			return State.DECREASE
		if signal == Signal.OVER_USE and self.state == State.INCREASE:
			return State.DECREASE
		if signal == Signal.OVER_USE and self.state == State.DECREASE:
			return State.DECREASE
		
		if signal == Signal.NORMAL and self.state == State.HOLD:
			return State.INCREASE
		if signal == Signal.NORMAL and self.state == State.INCREASE:
			return State.INCREASE
		if signal == Signal.NORMAL and self.state == State.DECREASE:
			return State.HOLD
		
		if signal == Signal.UNDER_USE and self.state == State.HOLD:
			return State.HOLD
		if signal == Signal.UNDER_USE and self.state == State.INCREASE:
			return State.HOLD
		if signal == Signal.UNDER_USE and self.state == State.DECREASE:
			return State.HOLD
