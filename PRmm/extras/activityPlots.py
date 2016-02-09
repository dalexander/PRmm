import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import math

from PRmm.model import Region


# Plots showing the metrics used to determine the "activity" in a ZMW,
# as used by the Sequel HQRF impl


# Build a data frame of: pulse rate, baseline state occupancy, sandwich rate
# half-sandwich rate, ... mean labelQV

# This is too slow, work on it
RED, GREEN = 1, 0
color = { "A" : RED, "C" : RED, "G" : GREEN, "T": GREEN }

PRE_ALIGNMENT, IN_ALIGNMENT, POST_ALIGNMENT = 2, 1, 0


def isSandwich(prePulseFrames, channelBase):
    # vectorized computation of indicator variable for sandwich event.
    # the middle pulse is designated the sandwich event, here.
    isSandwichArr = np.zeros(shape=len(channelBase), dtype=bool)
    for j in xrange(len(channelBase)):
        if j == 0 or j == (len(channelBase) - 1):
            isSandwichArr[j] = False
        else:
            adjacentWithPrev = prePulseFrames[j] == 0
            adjacentWithNext = prePulseFrames[j+1] == 0
            prevColor = color[channelBase[j-1]]
            thisColor = color[channelBase[j]]
            nextColor = color[channelBase[j+1]]

            isSandwichArr[j] = ((adjacentWithPrev and adjacentWithNext) and
                                (prevColor == nextColor) and (thisColor != prevColor))
    return isSandwichArr

def isHalfSandwich(prePulseFrames, channelBase):
    # vectorized computation of indicator variable for sandwich event.
    # the latter pulse is designated the sandwich event, here.
    isHalfSandwichArr = np.zeros(shape=len(channelBase), dtype=bool)
    for j in xrange(len(channelBase)):
        if j == 0:
            isHalfSandwichArr[j] = False
        else:
            adjacentWithPrev = prePulseFrames[j] == 0
            prevColor = color[channelBase[j-1]]
            thisColor = color[channelBase[j]]

            isHalfSandwichArr[j] = adjacentWithPrev and (thisColor != prevColor)
    return isHalfSandwichArr


def alignmentFrameExtent(zmwFixture):
    assert len(zmwFixture.alignments) == 1
    rr = zmwFixture.regions
    aln = [r for r in rr if r.regionType == Region.ALIGNMENT_REGION][0]
    return (aln.startFrame, aln.endFrame)


def computeMetrics(zmwFixture, epochFrames=4096):

    holeNumber = zmwFixture.holeNumber

    pulseRate          = []
    baselineOccupancy  = []
    sandwichRate       = []
    halfSandwichRate   = []
    meanPulseWidth     = []
    meanBasecallerQV   = []
    meanLabelQV        = []
    homopolymerContent = []
    meanSignal         = []

    # interval sizes...
    frameRate = zmwFixture.frameRate
    W_sec = float(epochFrames)/frameRate
    W_frames = epochFrames
    n_W = int(zmwFixture.numFrames / W_frames)

    # minimum num pulses to emit averages of pulse metrics
    MIN_PULSES = 10

    for i in xrange(n_W):

        frameExtent = (W_frames*i, W_frames*(i+1))
        # pulse rate
        pulseExtent = zmwFixture.pulseIntervalFromFrames(*frameExtent)
        pulseSlice = slice(*pulseExtent)
        pulseRate.append((pulseExtent[1] - pulseExtent[0])/float(W_sec))

        # pulses
        pulses         = zmwFixture.pulseLabel     [pulseSlice]
        pulseWidth     = zmwFixture.pulseWidth     [pulseSlice]
        prePulseFrames = zmwFixture.prePulseFrames [pulseSlice]
        pulseLabelQV   = zmwFixture.pulseLabelQV   [pulseSlice]
        pulsePkmean    = zmwFixture.pulsePkmean    [pulseSlice]
        pulseChannel   = zmwFixture.pulseChannel   [pulseSlice]

        # median pulseWidth
        if len(pulses) > MIN_PULSES:
            meanPulseWidth.append(np.mean(pulseWidth))
        else:
            meanPulseWidth.append(np.nan)

        # mean label QV
        if len(pulses) > MIN_PULSES:
            meanLabelQV.append(np.mean(pulseLabelQV))
        else:
            meanLabelQV.append(np.nan)

        # mean signal, reckoned as the average of pulse MeanSignal
        # divided by the channel BaselineSigma

        # TODO: restore this.  Hopeless ATM because we aren't storing baseline sigma
        # in the BAM file yet.
        # if len(pulses) > MIN_PULSES:
        #     idx = np.arange(len(pulses))
        #     signals = pulses.meanSignal()[idx, pulses.channel()] / plsZmw.baselineSigma()[pulses.channel()]
        #     meanSignal.append(np.mean(signals))
        # else:
        #     meanSignal.append(np.nan)
        meanSignal.append(0.0)

        # homopolymer content, in the *pulse* calls
        # reckoned as empirical probability that pulseLabel[i] == pulseLabel[i-1]
        curChannel = pulseChannel
        prevChannel = np.pad(pulseChannel, (1,0), "constant", constant_values=(-1,))[:-1]
        if len(pulses) > MIN_PULSES:
            hpc = np.mean(curChannel == prevChannel)
        else:
            hpc = np.nan
        homopolymerContent.append(hpc)

        # Update: using simple Laplace rule regularization to shrink to the random
        # expected 0.25---this is because we see it dropping to zero in windows where
        # pulseRate was ~zero.  Want to represent "ignorance" better by shrinkage to 0.25;
        # this will keep distribution unimodal under P0 condition.
#         homopolymerContent.append((sum(curChannel == prevChannel) + 5) /
#                                   float(len(curChannel)          + 20))

        # Rate or count of sandwiches?
        # Count gets rid of the ugly hyperbolic appearance of the plot
        #sandwichRate.append(sum(isSandwich))
        if len(pulses) > MIN_PULSES:
            sandwichRate.append(np.mean(isSandwich(prePulseFrames, pulses)))
            halfSandwichRate.append(np.mean(isHalfSandwich(prePulseFrames, pulses)))
        else:
            sandwichRate.append(np.nan)
            halfSandwichRate.append(np.nan)

        #a = zmwFixture.alignments[0]
        #b = zmwFixture.baseLabel[a.rStart:a.rEnd]
        #alnExtent = np.array(alignmentFrameExtent(zmwFixture))/ W_frames

        state = np.zeros_like(homopolymerContent)
        # state = []
        # for i in xrange(n_W):
        #     alnStart, alnEnd = alnExtent
        #     afterAlnStart = i   >= alnStart
        #     beforeAlnEnd  = i+1 <= alnEnd
        #     if   afterAlnStart and beforeAlnEnd: s = IN_ALIGNMENT
        #     elif not afterAlnStart:              s = PRE_ALIGNMENT
        #     else:                                s = POST_ALIGNMENT
        #     state.append(s)


    return pd.DataFrame({ "HoleNumber"             : holeNumber,
                          "Epoch"                  : np.arange(n_W),
#                          "BaselineStateOccupancy" : baselineOccupancy,
                          "PulseRate"              : pulseRate,
                          "SandwichRate"           : sandwichRate,
                          "HalfSandwichRate"       : halfSandwichRate,
                          "MeanPulseWidth"         : meanPulseWidth,
#                          "MeanBasecallQV"         : meanBasecallerQV,
                          "MeanLabelQV"            : meanLabelQV,
                          "MeanSignal"             : meanSignal,
                          "HomopolymerContent"     : homopolymerContent,
                          "State"                  : state})



def plotMetrics(zmwFixture, epochFrames=4096):

    # interval sizes...
    frameRate = zmwFixture.frameRate
    W_sec = float(epochFrames)/frameRate
    W_frames = epochFrames
    n_W = int(zmwFixture.numFrames / W_frames)

    metrics = computeMetrics(zmwFixture, epochFrames)

    assert len(zmwFixture.alignments) <= 1
    hasAlignment = len(zmwFixture.alignments) == 1
    # if hasAlignment:
    #     a = zmwFixture.alignments[0]
    #b = zmwFixture.baseLabel[a.rStart:a.rEnd]

    if hasAlignment:
        alnExtent = np.array(zmwFixture.traceRegions.alignment.extent) / W_frames
    hqExtent = np.array(zmwFixture.traceRegions.hqRegion.extent) / W_frames

    # details = "%d bp, %d bp @ %d%%, %d bp" %  \
    #           (a.rStart,
    #            a.rEnd  - a.rStart, 100*a.identity,
    #            zmwFixture.numBases - a.rEnd)
    details = ""

    fig = plt.figure(figsize=(12,10))
    red_patch = matplotlib.patches.Patch(color='red', label="Alignment")
    black_patch = matplotlib.patches.Patch(color='black', label="HQ region")
    fig.legend([red_patch, black_patch], ["Alignment", "HQ region"], "upper right")


    def makeSubplot(pane, metric, desc):
        plt.subplot(3, 2, pane)
        plt.plot(metrics.Epoch, metric, 'o')
        ax = plt.gca()
        ax.set_xlim(0, n_W)
        ymin, ymax = ax.get_ylim()
        #plt.vlines(alnExtent, *ax.get_ylim(), linewidth=1)
        #plt.vlines(hqExtent,  *ax.get_ylim(), linewidth=1, color="red")
        if hasAlignment:
            plt.hlines(ymax, alnExtent[0], alnExtent[1], linewidth=4, color="red")
        plt.hlines(ymin, hqExtent[0],  hqExtent[1],  linewidth=4, color="black")

        plt.ylabel(desc)

    makeSubplot(1, metrics.HomopolymerContent, "Pulse homopolymer content")
    makeSubplot(3, metrics.PulseRate,          "Pulse rate")

    makeSubplot(5, metrics.HalfSandwichRate,   "Sandwich & half sandwich rates")
    plt.plot(metrics.Epoch, metrics.SandwichRate)

    makeSubplot(2, metrics.MeanPulseWidth,     "Mean pulse width")
    makeSubplot(4, metrics.MeanSignal,         "Mean signal")
    makeSubplot(6, metrics.MeanLabelQV,        "Mean LabelQV")

    plt.suptitle(zmwFixture.zmwName + "\n" + details, fontsize=16)
