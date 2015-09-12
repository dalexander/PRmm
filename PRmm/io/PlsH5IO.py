
__all__ = [ "PlxH5Reader", "BasecallsUnavailable" ]

from pbcore.io.BasH5IO import (_makeOffsetsDataStructure, arrayFromDataset, BaxH5Reader)

import h5py
import numpy as np
import os.path as op
from bisect import bisect_left, bisect_right


class BasecallsUnavailable(Exception): pass

class PlxZmw(object):
    __slots__ = [ "plxH5", "holeNumber", "plxIndex", "baxPeer", "pulseIndex" ]

    def __init__(self, plxH5, holeNumber):
        self.holeNumber = holeNumber
        self.plxH5 = plxH5
        self.plxIndex = self.plxH5._holeNumberToIndex[holeNumber]
        if self.plxH5.baxPeer:
            self.baxPeer = self.plxH5.baxPeer[holeNumber]
            self.pulseIndex = self.baxPeer.readNoQC().PulseIndex()
        else:
            self.baxPeer = None

    @property
    def _offsets(self):
        return self.plxH5._offsetsByHole[self.holeNumber]

    @property
    def baseMap(self):
        return self.plxH5.baseMap

    def baseline(self):
        # Cache this, or the array, upstream?
        return self.plxH5._pulsecallsZmwGroup["BaselineLevel"][self.plxIndex,:]

    def baselineSigma(self):
        # Cache this, or the array, upstream?
        return self.plxH5._pulsecallsZmwGroup["BaselineSigma"][self.plxIndex,:]

    def pulsesByPulseInterval(self, beginPulse, endPulse):
        return ZmwPulses(self, self.holeNumber, beginPulse, endPulse)

    def pulsesByFrameInterval(self, beginFrame, endFrame):
        # TODO: need to optimize this
        pcg = self.plxH5._pulsecallsGroup
        startFrame_    = arrayFromDataset(pcg["StartFrame"],    *self._offsets)
        widthInFrames_ = arrayFromDataset(pcg["WidthInFrames"], *self._offsets)
        endFrame_ = startFrame_ + widthInFrames_
        # find interval
        beginPulse = bisect_left(startFrame_, beginFrame)
        endPulse   = bisect_right(endFrame_, endFrame)
        return ZmwPulses(self, self.holeNumber, beginPulse, endPulse)

    def pulses(self):
        return ZmwPulses(self, self.holeNumber)


class ZmwPulses(object):

    __slots__ = [ "plxZmw", "holeNumber",
                  "pulseStart", "pulseEnd",
                  "offsetBegin", "offsetEnd",
                  "baxPeer", "baseStart", "baseEnd"  ]

    def __init__(self, plxZmw, holeNumber, pulseStart=None, pulseEnd=None):
        self.plxZmw      = plxZmw
        self.holeNumber  = holeNumber
        zmwOffsetBegin, zmwOffsetEnd = self.plxZmw._offsets
        if (pulseStart is not None) and (pulseEnd is not None):
            self.pulseStart  = pulseStart
            self.pulseEnd    = pulseEnd
        else:
            self.pulseStart  = 0
            self.pulseEnd    = zmwOffsetEnd - zmwOffsetBegin
        # Find pulse offsets
        self.offsetBegin = zmwOffsetBegin + self.pulseStart
        self.offsetEnd   = zmwOffsetBegin + self.pulseEnd
        if not (zmwOffsetBegin      <=
                self.offsetBegin <=
                self.offsetEnd   <=
                zmwOffsetEnd):
            raise IndexError, "Invalid slice of PlxZmw!"
        # If we have basecall info, find base interval
        if self.plxZmw.baxPeer:
            self.baseStart = bisect_left(self.plxZmw.pulseIndex,  self.pulseStart)
            self.baseEnd = bisect_right(self.plxZmw.pulseIndex, self.pulseEnd)

    @property
    def _pulsecallsGroup(self):
        return self.plxZmw.plxH5._pulsecallsGroup

    @property
    def offsets(self):
        return (self.offsetBegin, self.offsetEnd)

    @property
    def baseMap(self):
        return self.plxZmw.baseMap

    def channel(self):
        return arrayFromDataset(self._pulsecallsGroup["Channel"], *self.offsets)

    def channelBases(self):
        CHANNEL_BASES = np.fromstring(self.baseMap, dtype=np.uint8)
        return CHANNEL_BASES[self.channel()].tostring()


    def startFrame(self):
        return arrayFromDataset(self._pulsecallsGroup["StartFrame"], *self.offsets)

    def widthInFrames(self):
        return arrayFromDataset(self._pulsecallsGroup["WidthInFrames"], *self.offsets)

    def endFrame(self):
        return self.startFrame() + self.widthInFrames()


    def prePulseFrames(self):
        # This is a bit tricky.  Basically we want startFrame - lag(endFrame)
        # sfp = startframeprevious, etc.
        if self.offsetBegin == 0:
            efp = np.hstack([[0], self.endFrame()[:-1]])
        else:
            sfp = arrayFromDataset(self._pulsecallsGroup["StartFrame"],
                                   self.offsetBegin - 1, self.offsetEnd - 1)
            wfp = arrayFromDataset(self._pulsecallsGroup["WidthInFrames"],
                                   self.offsetBegin - 1, self.offsetEnd - 1)
            efp = sfp + wfp
        return self.startFrame() - efp

    def midSignal(self):
        return arrayFromDataset(self._pulsecallsGroup["MidSignal"], *self.offsets)

    def meanSignal(self):
        return arrayFromDataset(self._pulsecallsGroup["MeanSignal"], *self.offsets)

    def maxSignal(self):
        return arrayFromDataset(self._pulsecallsGroup["MaxSignal"], *self.offsets)

    def isCrfPulse(self):
        return arrayFromDataset(self._pulsecallsGroup["IsPulse"], *self.offsets)

    def isBase(self):
        """
        Use a peer bax file to see whether this pulse was deemed a base by
        P2B
        """
        if self.plxZmw.baxPeer is None:
            raise BasecallsUnavailable()
        else:
            # for pi in [pulseStart, pulseEnd]:
            #    is pi in self.plxZmw.pulseIndex[baseStart:baseEnd]?
            return np.in1d(np.arange(self.pulseStart, self.pulseEnd, dtype=int),
                           self.plxZmw.pulseIndex[self.baseStart:self.baseEnd])

    def __len__(self):
        return self.pulseEnd - self.pulseStart



class PlxH5Reader(object):

    def __init__(self, filename, bax=None):
        self.filename = op.abspath(op.expanduser(filename))
        self.file = h5py.File(self.filename, "r")
        self.baseMap = self.file["/ScanData/DyeSet"].attrs["BaseMap"][:]
        self._pulsecallsGroup = self.file["/PulseData/PulseCalls"]
        self._pulsecallsZmwGroup = self.file["/PulseData/PulseCalls/ZMW"]
        self._pulsecallsZmwMetrics = self.file["/PulseData/PulseCalls/ZMWMetrics"]
        holeNumbers = self._pulsecallsGroup["ZMW/HoleNumber"][:]
        self._holeNumberToIndex = dict(zip(holeNumbers, range(len(holeNumbers))))
        self._offsetsByHole = _makeOffsetsDataStructure(self._pulsecallsGroup)
        if bax is None:
            self.baxPeer = None
        elif isinstance(bax, str):
            self.baxPeer = BaxH5Reader(baxFilename)
        else:
            self.baxPeer = bax

    def __getitem__(self, holeNumber):
        return PlxZmw(self, holeNumber)
