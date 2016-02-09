# hmmlearn 0.1.1
from hmmlearn.hmm import MultinomialHMM
import json, numpy as np, pandas


# Activity enums
A0          = 0
A1          = 1
A2          = 2
nSymbols    = 3

# State enum
PRE         = 0
HQ          = 1
POST_QUIET  = 2
POST_ACTIVE = 3
nStates     = 4


def labelWindowsFromMetrics(metrics):
    # Metrics -> [ Activity ]
    pass

def labelWindowsFromBazViewerJson(bazZmwJson, hn, frameRate=80.0):
    j = json.load(open(bazZmwJson))
    hns = [ p["ZMW_NUMBER"] for p in j["METRICS"] ]
    idx = hns.index(hn)
    mfMetrics = j["METRICS"][idx]["MF_METRICS"]
    df = pandas.DataFrame.from_records(mfMetrics)
    halfSandwichRate = df.NUM_HALF_SANDWICHES / df.NUM_PULSES
    pulseRate = df.NUM_PULSES / (df.NUM_FRAMES / frameRate)
    labelStutterRate = df.NUM_PULSE_LABEL_STUTTERS / df.NUM_PULSES
    labels = [-1] * len(df)
    for i in xrange(len(df)):
        if   (pulseRate[i] <= 0.5 or labelStutterRate[i] >= 0.6): labels[i] = A0
        elif (halfSandwichRate[i]>= 0.06):                        labels[i] = A2
        else:                                                     labels[i] = A1
    return labels

def initHMM(length):
    a = 1.0 / length

    # Transition probabilities
    trans = np.array([[1-a,   a,   0,   0],   # Pre ->
                      [  0, 1-a, a/2, a/2],   # HQ  ->
                      [  0,   0,   1,   0],   # PostQuiet ->
                      [  0,   0,   0,   1] ]) # PostActive ->

    # Emission probabilities
    emit = np.array([[ 0.25, 0.25, 0.50 ],    # Emit | Pre
                     [ 0.20, 0.75, 0.05 ],    # Emit | HQ
                     [ 0.70, 0.15, 0.15 ],    # Emit | PostQuiet
                     [ 0.25, 0.25, 0.50 ] ])  # Emit | PostActive
    #                   A0    A1    A2

    # Start state distribution
    start = np.array([0.33, 0.33, 0.33, 0])

    hmm = MultinomialHMM(n_components=nStates)
    # hmmlearn API seems deficient here...
    hmm.transmat_ = trans
    hmm.startprob_ = start
    hmm.emissionprob_ = emit
    return hmm

def findHQR(labelSequence):
    pass



#def main():

# if __name__ == "__main__":
#     main()


labels = labelWindowsFromBazViewerJson("/home/UNIXHOME/dalexander/Projects/Bugs/Dromedary-HQRF/ZMW-11272631/11272631.json", 11272631)
hmm = initHMM(len(labels))
print hmm.predict(labels)
# This is bogus---not allowed to transition into and out of HQRF!
