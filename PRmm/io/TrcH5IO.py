__all__ = [ "TrxH5Reader" ]

import h5py
import os.path as op
import numpy as np


class HoleStatus(object):
    (SEQUENCING, ANTIHOLE, FIDUCIAL, SUSPECT,
     ANTIMIRROR, FDZMW, FBZMW, ANTIBEAMLET, OUTSIDEFOV) = range(9)

class TrxH5Reader(object):
    """
    Reader for trx.h5 files
    """
    def __init__(self, fname):
        self.filename = op.abspath(op.expanduser(fname))
        self.file = h5py.File(self.filename, "r")
        self._traceData = self.file["/TraceData/Traces"]
        self._initCodec()
        self._initHoleNumberMaps()

    def _initCodec(self):
        if "/TraceData/Codec/Decode" in self.file:
            self._codec = LutCodec(self.file["/TraceData/Codec/Decode"])
        else:
            assert self._traceData.dtype in (np.float32, np.int16)
            self._codec = NoOpCodec()

    def _initHoleNumberMaps(self):
        holeNumbers = self.file["/TraceData/HoleNumber"][:]
        self._holeNumbers = holeNumbers
        self._holeNumberToIndex = dict(zip(holeNumbers, range(len(holeNumbers))))

    @property
    def representation(self):
        return self.file["/TraceData"].attrs["Representation"]

    @property
    def numChannels(self):
        return self._traceData.shape[1]

    @property
    def movieName(self):
        return self.file["/ScanData/RunInfo"].attrs["MovieName"]

    @property
    def platformName(self):
        return self.file["/ScanData/RunInfo"].attrs["PlatformName"]

    @property
    def frameRate(self):
        return self.file["/ScanData/AcqParams"].attrs["FrameRate"]

    @property
    def movieLengthInFrames(self):
        return self._traceData.shape[2]

    @property
    def movieLength(self):
        return float(self.movieLengthInFrames) / self.frameRate

    @property
    def holeNumbers(self):
        return self._holeNumbers

    @property
    def codec(self):
        return self._codec

    def __getitem__(self, holeNumber):
        idx = self._holeNumberToIndex[holeNumber]
        arr = self._traceData[idx]
        return self.codec.decode(arr)


class LutCodec(object):
    def __init__(self, lut):
        self._lut = lut[:]

    def decode(self, arr):
        return self._lut[arr]

class NoOpCodec(object):
    def __init__(self):
        pass

    def decode(self, arr):
        # assert it's 16 bit
        return arr
