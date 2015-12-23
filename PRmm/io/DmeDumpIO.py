__all__ = [ "DmeDumpReader" ]

import h5py, numpy as np, os.path as op
from PRmm.model.utils import cached

class DmeDumpReader(object):

    # TODO: automatically prune 0-size blocks

    def __init__(self, fname):
        self.filename = op.abspath(op.expanduser(fname))
        self.file = h5py.File(self.filename, "r")
        self.holeNumber      = self.file["/HoleNumber"][:]                     # [nZmws]
        self.blockSize       = self.file["/BlockSize"][:]                      # [nBlocks]
        self.startFrame      = self.file["/StartFrame"][:]                     # [nBlocks]
        self.endFrame        = self.file["/EndFrame"][:]                       # [nBlocks]
        self.baseline        = self.file["/BaselineMean"]                      # [nBlocks][nZmws][nCam]
        self.mean            = self.file["/SmoothedEstimates/Mean"]            # [nBlocks][nZmws][nComp][nCam]
        self.covariance      = self.file["/SmoothedEstimates/Covariance"]      # [nBlocks][nZmws][nComp][numCvr(nCam)]
        self.mixtureFraction = self.file["/SmoothedEstimates/MixtureFraction"] # [nBlocks][nZmws][nComp]

        self._holeIndexLookup = dict(zip(self.holeNumber,
                                         xrange(len(self.holeNumber))))

    def lookupHoleIndex(self, hn):
        return self._holeIndexLookup[hn]

    def hole(self, hn):
        return DmeDumpHoleNumberSlice(self, hn)


class DmeDumpHoleNumberSlice(object):
    def __init__(self, reader, hn):
        self.reader = reader
        self.holeNumber = hn
        hnIndex = reader.lookupHoleIndex(hn)
        self.blockSize       = reader.blockSize
        self.startFrame      = reader.startFrame
        self.endFrame        = reader.endFrame
        self.baseline        = reader.baseline        [:,hnIndex,...]
        self.mean            = reader.mean            [:,hnIndex,...]
        self.covariance      = reader.covariance      [:,hnIndex,...]
        self.mixtureFraction = reader.mixtureFraction [:,hnIndex,...]


class DmeDumpBlockSlice(object):
    def __init__(self, reader, block):
        pass
