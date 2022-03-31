from enum import Enum


class State(Enum):
	HOLD = "Hold"
	INCREASE = "Increase"
	DECREASE = "Decrease"


class Signal(Enum):
	OVER_USE = "Overuse"
	NORMAL = "Normal"
	UNDER_USE = "Underuse"


class interfaceState(Enum):
	INIT = "init"
	REPORT = "report"
	ESTIMATE = "estimate"
