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
	INIT = "init4Test"
	REPORT = "report"
	ESTIMATE = "estimate"


class aimdType(Enum):
	MAX_UNKNOWN = "max_unknown"
	NEAR_MAX = "near_max"


class bbrType(Enum):
	START_UP = "start_up"
	RETREAT = "retreat"
	RECOVERY = "recovery"
	INIT = "init4Test"
	QUIT = "quit"


class traceAttr(Enum):
	def __str__(self):
		return str(self.value)
	
	CAP = "capacity"
	DELAY = "delay"


class myFilePath(Enum):
	ORI_TRACE = "./mytraces/ori_traces"


class ccAlgo(Enum):
	GCC = "GCCmyself"  # gcc-native with filter-type-none
	HRCC = "RTSRule"  # gcc-hrcc-trendline
	RTSDRL = "RTSDrl"  # drl-07
	RTSHY = "RTSHybird"  # drl mix hrcc
	GEMINI = "GCCGEMINI"  # gcc-gemini magic trendline
	RTSRule = "RTSRulev2"  # todo: bbr
	HRCC_KAL = "HRCCkalman"  #


class traceSetType(Enum):
	WIRED = "WIRED"
	LTE = "LTE"
	REAL = "REAL"  # 427
	REAL_SPECIAL = "REAL_SPECIAL"  # 2,11,45,9
