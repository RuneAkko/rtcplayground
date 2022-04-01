from plot.drawCurve import Line
from plot.drawCurve import draw
from rtc_env import GymEnv
from utils.trace_analyse import getTrace


def ruleEstimatorTest(path):
    """

    :return:
    """
    env = GymEnv()
    name, _ = getTrace(path)
    env.set(path)

    max_step = 100000
    traceDone = None
    step = 0
    qosList = [0]
    stepList = [step]

    rate = env.ruleEstimator.predictionBandwidth
    targetRate = [rate]

    while not traceDone and step < max_step:
        rate, traceDone, qos1,qos2,qos3,qos4 = env.test(rate,step)
        qosList.append(qos1)
        step += 1
        stepList.append(step)
        targetRate.append(rate)

    # realRate = Line()
    # realRate.name = "cap"
    gccRate = Line()
    gccRate.name = "targetRate"
    gccRate.x = stepList
    gccRate.y = targetRate

    draw(gccRate)

    recvRate = Line()
    recvRate.name = "recvRate"
    recvRate.x = stepList
    recvRate.y = qosList
    draw(recvRate)

    with open("testGccRate.txt","w") as f:
        f.write(str(gccRate.y))
    with open("testRecvRate.txt","w") as f:
        f.write(str(recvRate.y))

testTracePath = "./traces/4G_500kbps.json"
ruleEstimatorTest(testTracePath)
