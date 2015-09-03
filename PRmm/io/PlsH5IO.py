
__all__ = [ "PlxH5Reader" ]

from pbcore.io.BasH5IO import (_makeOffsetsDataStructure, arrayFromDataset, BaxH5Reader)

import h5py
import numpy as np
import os.path as op
from bisect import bisect_left, bisect_right


class PlxZmw(object):
    __slots__ = [ "plxH5", "holeNumber", "plxIndex", "baxPeer", "pulseIndex" ]

    def __init__(self, plxH5, holeNumber):
        #super(PlxZmw, self).__init__(plxH5, holeNumber)
        self.holeNumber = holeNumber
        self.plxH5 = plxH5
        self.plxIndex = self.plxH5._plxHoleNumberToIndex[holeNumber]
        if self.plxH5.baxPeer:
            self.baxPeer = self.plxH5.baxPeer[holeNumber]
            self.pulseIndex = self.baxPeer.readNoQC().PulseIndex()
        else:
            self.baxPeer = None

    @property
    def _plxOffsets(self):
        return self.plxH5._plxOffsetsByHole[self.holeNumber]

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
        startFrame_    = arrayFromDataset(pcg["StartFrame"],    *self._plxOffsets)
        widthInFrames_ = arrayFromDataset(pcg["WidthInFrames"], *self._plxOffsets)
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
                  "plxOffsetBegin", "plxOffsetEnd",
                  "baxPeer", "baseStart", "baseEnd"  ]

    def __init__(self, plxZmw, holeNumber, pulseStart=None, pulseEnd=None):
        self.plxZmw      = plxZmw
        self.holeNumber  = holeNumber
        zmwOffsetBegin, zmwOffsetEnd = self._getPlxOffsets()[self.holeNumber]
        if (pulseStart is not None) and (pulseEnd is not None):
            self.pulseStart  = pulseStart
            self.pulseEnd    = pulseEnd
        else:
            self.pulseStart  = 0
            self.pulseEnd    = zmwOffsetEnd - zmwOffsetBegin
        # Find pulse offsets
        self.plxOffsetBegin = zmwOffsetBegin + self.pulseStart
        self.plxOffsetEnd   = zmwOffsetBegin + self.pulseEnd
        if not (zmwOffsetBegin      <=
                self.plxOffsetBegin <=
                self.plxOffsetEnd   <=
                zmwOffsetEnd):
            raise IndexError, "Invalid slice of PlxZmw!"
        # If we have basecall info, find base interval
        if self.plxZmw.baxPeer:
            self.baseStart = bisect_left(self.plxZmw.pulseIndex,  self.pulseStart)
            self.baseEnd = bisect_right(self.plxZmw.pulseIndex, self.pulseEnd)

    @property
    def _pulsecallsGroup(self):
        return self.plxZmw.plxH5._pulsecallsGroup

    def _getPlxOffsets(self):
        return self.plxZmw.plxH5._plxOffsetsByHole

    def channel(self):
        return arrayFromDataset(self._pulsecallsGroup["Channel"],
                                self.plxOffsetBegin, self.plxOffsetEnd)
    def channelBases(self):
        CHANNEL_BASES = np.fromstring("TGAC", dtype=np.uint8)
        return CHANNEL_BASES[self.channel()].tostring()


    def startFrame(self):
        return arrayFromDataset(self._pulsecallsGroup["StartFrame"],
                                self.plxOffsetBegin, self.plxOffsetEnd)

    def widthInFrames(self):
        return arrayFromDataset(self._pulsecallsGroup["WidthInFrames"],
                                self.plxOffsetBegin, self.plxOffsetEnd)

    def endFrame(self):
        return self.startFrame() + self.widthInFrames()

    def midSignal(self):
        return arrayFromDataset(self._pulsecallsGroup["MidSignal"],
                                self.plxOffsetBegin, self.plxOffsetEnd)

    def meanSignal(self):
        return arrayFromDataset(self._pulsecallsGroup["MeanSignal"],
                                self.plxOffsetBegin, self.plxOffsetEnd)

    def maxSignal(self):
        return arrayFromDataset(self._pulsecallsGroup["MaxSignal"],
                                self.plxOffsetBegin, self.plxOffsetEnd)

    def isCrfPulse(self):
        return arrayFromDataset(self._pulsecallsGroup["IsPulse"],
                                self.plxOffsetBegin, self.plxOffsetEnd)

    def isBase(self):
        """
        Use a peer bax file to see whether this pulse was deemed a base by
        P2B
        """
        if self.plxZmw.baxPeer is None:
            raise RuntimeError, "basecalls unavailable"
        else:
            # for pi in [pulseStart, pulseEnd]:
            #    is pi in self.plxZmw.pulseIndex[baseStart:baseEnd]?
            return np.in1d(np.arange(self.pulseStart, self.pulseEnd, dtype=int),
                           self.plxZmw.pulseIndex[self.baseStart:self.baseEnd])

    def __len__(self):
        return self.pulseEnd - self.pulseStart

class PlxH5Reader(object):

    def __init__(self, filename, baxFilename=None):
        self.filename = op.abspath(op.expanduser(filename))
        self.file = h5py.File(self.filename, "r")
        self._pulsecallsGroup = self.file["/PulseData/PulseCalls"]
        self._pulsecallsZmwGroup = self.file["/PulseData/PulseCalls/ZMW"]
        self._pulsecallsZmwMetrics = self.file["/PulseData/PulseCalls/ZMWMetrics"]
        holeNumbers = self._pulsecallsGroup["ZMW/HoleNumber"][:]
        self._plxHoleNumberToIndex = dict(zip(holeNumbers, range(len(holeNumbers))))
        self._plxOffsetsByHole = _makeOffsetsDataStructure(self._pulsecallsGroup)

        if baxFilename is None:
            self.baxPeer = None
        else:
            self._openBaxPeer(baxFilename)

    def _openBaxPeer(self, baxFilename):
        self.baxPeer = BaxH5Reader(baxFilename)

    def __getitem__(self, holeNumber):
        return PlxZmw(self, holeNumber)
