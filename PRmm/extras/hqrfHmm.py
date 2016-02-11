# We require hmmlearn 0.2.0, which is not yet released, because of
# bugfixes---especially the removal of compulsory "normalization" that
# was destroying the structure of the transition matrix.
from hmmlearn.hmm import MultinomialHMM
import h5py, json, numpy as np, pandas as pd


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


def loadBazViewerHDF5(h5Filename, frameRateHz=80.0):
    h5 = h5py.File(h5Filename, "r")
    mf = h5["MFMetrics"]
    mapping = { k : mf[k][:] for k in mf }
    df = pd.DataFrame.from_dict(mapping)
    # Augment columns
    df["HalfSandwichRate"] = df.NUM_HALF_SANDWICHES.astype(np.float) /  df.NUM_PULSES
    df["PulseRate"] = df.NUM_PULSES.astype(np.float) / (df.NUM_FRAMES / frameRateHz)
    df["LabelStutterRate"] = df.NUM_PULSE_LABEL_STUTTERS.astype(np.float) / df.NUM_PULSES
    return df

def labelWindows(df, hn):
    dfZ = df[df.ZmwNumber == hn]
    labels = [-1] * len(dfZ)
    for i in xrange(len(dfZ)):
        if   (dfZ.PulseRate.iloc[i] <= 0.5 or dfZ.LabelStutterRate.iloc[i] >= 0.6):
            labels[i] = A0
        elif (dfZ.HalfSandwichRate.iloc[i] >= 0.06):
            labels[i] = A2
        else:
            labels[i] = A1
    return np.reshape(labels, (-1, 1))

def initHMM(length):
    a = 1.0 / length

    # Transition probabilities
    trans = np.array([[1-a,   a,   0,   0],   # Pre ->
                      [  0, 1-a, a/2, a/2],   # HQ  ->
                      [  0,   0,   1,   0],   # PostQuiet ->
                      [  0,   0,   0,   1] ]) # PostActive ->

    # emission probabilities
    emit = np.array([[ 0.25, 0.25, 0.50 ],    # Emit | Pre
                     [ 0.20, 0.75, 0.05 ],    # Emit | HQ
                     [ 0.70, 0.15, 0.15 ],    # Emit | PostQuiet
                     [ 0.25, 0.25, 0.50 ] ])  # Emit | PostActive
    #                   A0    A1    A2

    # Start state distribution
    start = np.array([0.34, 0.33, 0.33, 0])

    hmm = MultinomialHMM(n_components=nStates)
    hmm.transmat_ = trans
    hmm.startprob_ = start
    hmm.emissionprob_ = emit
    return hmm

def findHQR(labelSequence):
    hmm = initHMM(len(labelSequence))
    ll, inferredStates = hmm.decode(labelSequence)
    # find the extent of HQ
    print inferredStates

#def main():

# if __name__ == "__main__":
#     main()


#labels = labelWindowsFromBazViewerJson("/home/UNIXHOME/dalexander/Projects/Bugs/Dromedary-HQRF/ZMW-11272631/11272631.json", 11272631)
#labels = labelWindowsFromBazViewerJson("/tmp/11272631.json", 11272631)
df = loadBazViewerHDF5("/tmp/X1E3_metrics.h5")

labels = labelWindows(df, 10944688)

print labels.ravel()
hmm = initHMM(len(labels))
decoded = hmm.decode(labels)
print decoded

print decoded[1]
