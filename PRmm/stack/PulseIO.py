
__all__ = [ "PlxH5Reader" ]

from pbcore.io.BasH5IO import (_makeOffsetsDataStructure, arrayFromDataset)

import h5py
import numpy as np
import os.path as op
from bisect import bisect_left, bisect_right


class PlxZmw(object):
    __slots__ = [ "plxH5", "holeNumber", "plxIndex" ]

    def __init__(self, plxH5, holeNumber):
        #super(PlxZmw, self).__init__(plxH5, holeNumber)
        self.holeNumber = holeNumber
        self.plxH5 = plxH5
        self.plxIndex = self.plxH5._plxHoleNumberToIndex[holeNumber]

    @property
    def _plxOffsets(self):
        return self.plxH5._plxOffsetsByHole[self.holeNumber]

    def baseline(self):
        pass

    def baselineSigma(self):
        pass

    def holeXY(self):
        pass

    def pulsesByBaseInterval(self, beginBase, endBase):
        # TODO: this is now broken...
        pulseIndex = self.readNoQC().PulseIndex()
        pulseStart = pulseIndex[beginBase]
        pulseEnd   = pulseIndex[endBase]
        return ZmwPulses(self.plxH5, self.holeNumber, pulseStart, pulseEnd)

    def pulsesByPulseInterval(self, beginPulse, endPulse):
        return ZmwPulses(self.plxH5, self.holeNumber, beginPulse, endPulse)

    def pulsesByFrameInterval(self, beginFrame, endFrame):
        # TODO: need to optimize this
        pcg = self.plxH5._pulsecallsGroup
        startFrame_    = arrayFromDataset(pcg["StartFrame"],    *self._plxOffsets)
        widthInFrames_ = arrayFromDataset(pcg["WidthInFrames"], *self._plxOffsets)
        endFrame_ = startFrame_ + widthInFrames_
        # find interval
        beginPulse = bisect_left(startFrame_, beginFrame)
        endPulse   = bisect_right(endFrame_, endFrame)
        return ZmwPulses(self.plxH5, self.holeNumber, beginPulse, endPulse)


    # metrics? pulserate, pulseratevst


class ZmwPulses(object):

    __slots__ = [ "plxH5", "holeNumber",
                  "pulseStart", "pulseEnd",
                  "plxOffsetBegin", "plxOffsetEnd" ]

    def __init__(self, plxH5, holeNumber, pulseStart, pulseEnd):
        self.plxH5       = plxH5
        self.holeNumber  = holeNumber
        self.pulseStart  = pulseStart
        self.pulseEnd    = pulseEnd
        zmwOffsetBegin, zmwOffsetEnd = self._getPlxOffsets()[self.holeNumber]
        self.plxOffsetBegin = zmwOffsetBegin + self.pulseStart
        self.plxOffsetEnd   = zmwOffsetBegin + self.pulseEnd
        if not (zmwOffsetBegin   <=
                self.plxOffsetBegin <=
                self.plxOffsetEnd   <=
                zmwOffsetEnd):
            raise IndexError, "Invalid slice of PlxZmw!"

    @property
    def _pulsecallsGroup(self):
        return self.plxH5._pulsecallsGroup

    def _getPlxOffsets(self):
        return self.plxH5._plxOffsetsByHole

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
        pass

    def maxSignal(self):
        pass

    def isPulse(self):
        """
        Is the pulse actually a pulse? No idea why Pat did this.
        """
        pass

    def isBase(self):
        """
        Did the pulse make it to a basecall?
        """
        pass

    def __len__(self):
        return self.pulseEnd - self.pulseStart

class PlxH5Reader(object):

    def __init__(self, filename):
        self.filename = op.abspath(op.expanduser(filename))
        self.file = h5py.File(self.filename, "r")
        self._pulsecallsGroup = self.file["/PulseData/PulseCalls"]
        self._pulsecallsZmwGroup = self.file["/PulseData/PulseCalls/ZMW"]
        self._pulsecallsZmwMetrics = self.file["/PulseData/PulseCalls/ZMWMetrics"]
        holeNumbers = self._pulsecallsGroup["ZMW/HoleNumber"][:]
        self._plxHoleNumberToIndex = dict(zip(holeNumbers, range(len(holeNumbers))))
        self._plxOffsetsByHole = _makeOffsetsDataStructure(self._pulsecallsGroup)

    def __getitem__(self, holeNumber):
        return PlxZmw(self, holeNumber)
