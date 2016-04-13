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


# def safeDivide(num, den):
#     return np.ifelse(

def loadBazViewerHDF5(h5Filename, frameRateHz=80.0):
    h5 = h5py.File(h5Filename, "r")
    mf = h5["MFMetrics"]
    mapping = { k : mf[k][:] for k in mf }
    df = pd.DataFrame.from_dict(mapping)
    # Augment columns
    df["HalfSandwichRate"] = df.NUM_HALF_SANDWICHES.astype(np.float) /  df.NUM_PULSES
    df["SandwichRate"] = df.NUM_SANDWICHES.astype(np.float) /  df.NUM_PULSES
    df["PulseRate"] = df.NUM_PULSES.astype(np.float) / (df.NUM_FRAMES / frameRateHz)
    df["LabelStutterRate"] = df.NUM_PULSE_LABEL_STUTTERS.astype(np.float) / df.NUM_PULSES
    df["MeanPulseWidth"] = df.PULSE_WIDTH / df.NUM_PULSES
    return df


class DromedaryHQRegionFinder(object):
    """
    A Python implementation of the HQRF we shipped in Dromedary.
    """
    def labelWindows(self, dfZ):
        labels = [-1] * len(dfZ)
        for i in xrange(len(dfZ)):
            if   (dfZ.PulseRate.iloc[i] <= 0.5 or dfZ.LabelStutterRate.iloc[i] >= 0.6):
                labels[i] = A0
            elif (dfZ.HalfSandwichRate.iloc[i] >= 0.06):
                labels[i] = A2
            else:
                labels[i] = A1
        return np.reshape(labels, (-1, 1))

    def initHMM(self, length):
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

    def decodeHQR(self, labelSequence):
        hmm = self.initHMM(len(labelSequence))
        ll, inferredStates = hmm.decode(labelSequence)
        return inferredStates

    def findHQWindowSpan(self, dfZ):
        labelSequence = self.labelWindows(dfZ)
        decoded = self.decodeHQR(labelSequence)
        if 1 not in decoded:
            return (0, 0)
        else:
            # slow
            pos = np.flatnonzero(decoded == 1)
            return (min(pos), max(pos) + 1)

    def findHQRegion(self, df, hn):
        """
        Main entry point: (document this!)
        """
        dfZ = df[df.ZmwNumber == hn]
        basesSeen = [0] + list(np.cumsum(dfZ.NUM_BASES))
        wS, wE = self.findHQWindowSpan(dfZ)
        return (basesSeen[wS], basesSeen[wE])

class EnhancedHQRegionFinder(DromedaryHQRegionFinder):
    """
    A Python version of Dave's "enhanced" HQRF, which was intended to
    cull double-activity regions; changes as follows:

    - Use short mean pulse widths as an indicator of stick-dominated
      pulses in an empty hole (A0)
    - Use full-sandwiches as a strong indicator of A2
    - Make HQ and PostQuiet states less tolerant of A2 windows
    - If HQ region is called as a single window, force an empty HQR as
      it is probably an artifact of the model structure
    """
    def labelWindows(self, dfZ):
        labels = [-1] * len(dfZ)
        for i in xrange(len(dfZ)):
            if   (dfZ.PulseRate.iloc[i]        <= 0.5 or
                  dfZ.LabelStutterRate.iloc[i] >= 0.6 or
                  dfZ.MeanPulseWidth.iloc[i]   <= 4.0):
                labels[i] = A0
            elif (dfZ.HalfSandwichRate.iloc[i] >= 0.06):
                labels[i] = A2
            else:
                labels[i] = A1
        return np.reshape(labels, (-1, 1))

    def initHMM(self, length):
        a = 1.0 / length

        # Transition probabilities
        trans = np.array([[1-a,   a,   0,   0],   # Pre ->
                          [  0, 1-a, a/2, a/2],   # HQ  ->
                          [  0,   0,   1,   0],   # PostQuiet ->
                          [  0,   0,   0,   1] ]) # PostActive ->

        # emission probabilities
        eps = 1e-4
        emit = np.array([[ 0.25, 0.25, 0.50 ],    # Emit | Pre
                         [ 0.16, 0.84-eps, eps ], # Emit | HQ
                         [ 0.90, 0.10-eps, eps ], # Emit | PostQuiet
                         [ 0.25, 0.25, 0.50 ] ])  # Emit | PostActive
        #                   A0    A1    A2

        # Start state distribution
        start = np.array([0.34, 0.33, 0.33, 0])

        hmm = MultinomialHMM(n_components=nStates)
        hmm.transmat_ = trans
        hmm.startprob_ = start
        hmm.emissionprob_ = emit
        return hmm

    def findHQWindowSpan(self, dfZ):
        basicHQR = super(EnhancedHQRegionFinder, self).findHQWindowSpan(dfZ)
        s, e = basicHQR
        if e == s + 1:
            return (0, 0)
        else:
            return basicHQR

if __name__ == "__main__":
    df = loadBazViewerHDF5("/Users/dalexander/Data/m54012_160228_211932.metrics.h5")
    hn0 = 10944718
    dfZ = df[df.ZmwNumber == hn0]
    D = DromedaryHQRegionFinder()
    E = EnhancedHQRegionFinder()


    from PRmm.fixture import Fixture

    fx = Fixture.fromIniFile("/home/UNIXHOME/dalexander/Projects/Bugs/HQRF-echidna/RevertTransition/bcstream/fixtures.ini", "4")
    fxZ = fx[hn0]
