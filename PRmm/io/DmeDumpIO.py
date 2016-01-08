__all__ = [ "DmeDumpReader" ]

import h5py, numpy as np, os.path as op
from PRmm.model.utils import cached

class DmeDumpReader(object):

    # TODO: automatically prune 0-size blocks

    def __init__(self, fname):
        self.filename = op.abspath(op.expanduser(fname))
        self.file = h5py.File(self.filename, "r")

        self.holeNumber              = self.file["/HoleNumber"][:]                     # [nZmws]
        self.blockSize               = self.file["/BlockSize"][:]                      # [nBlocks]
        self.startFrame              = self.file["/StartFrame"][:]                     # [nBlocks]
        self.endFrame                = self.file["/EndFrame"][:]                       # [nBlocks]
        self.baseline                = self.file["/BaselineMean"]                      # [nBlocks][nZmws][nCam]
        self.baselineCovariance      = self.file["/BaselineCovariance"]                # [nBlocks][nZmws][nCvr]

        self.converged               = self.file["/RawEstimates/Converged"]            # [nBlocks][nZmws]
        self.iterations              = self.file["/RawEstimates/Iterations"]           # [nBlocks][nZmws]
        self.confidenceScore         = self.file["/RawEstimates/ConfidenceScore"]      # [nBlocks][nZmws]
        self.loglikelihood           = self.file["/RawEstimates/Loglikelihood"]        # [nBlocks][nZmws]
        self.deltaLoglikelihood      = self.file["/RawEstimates/DeltaLoglikelihood"]   # [nBlocks][nZmws]

        self.rawMean                 = self.file["/RawEstimates/Mean"]                 # [nBlocks][nZmws][nComp][nCam]
        self.rawCovariance           = self.file["/RawEstimates/Covariance"]           # [nBlocks][nZmws][nComp][nCvr]
        self.rawMixtureFraction      = self.file["/RawEstimates/MixtureFraction"]      # [nBlocks][nZmws][nComp]

        self.smoothedMean            = self.file["/SmoothedEstimates/Mean"]            # [nBlocks][nZmws][nComp][nCam]
        self.smoothedCovariance      = self.file["/SmoothedEstimates/Covariance"]      # [nBlocks][nZmws][nComp][nCvr]
        self.smoothedMixtureFraction = self.file["/SmoothedEstimates/MixtureFraction"] # [nBlocks][nZmws][nComp]

        self._holeIndexLookup = dict(zip(self.holeNumber,
                                         xrange(len(self.holeNumber))))

    def lookupHoleIndex(self, hn):
        return self._holeIndexLookup[hn]

    def hole(self, hn):
        return DmeDumpHoleNumberSlice(self, hn)

    def holeAndBlock(self, hn, block):
        return DmeDumpHoleNumberAndBlockSlice(self, hn, block)


class DmeDumpHoleNumberSlice(object):
    def __init__(self, reader, hn):
        self.reader = reader
        self.holeNumber = hn
        hnIndex = reader.lookupHoleIndex(hn)
        self.blockSize               = reader.blockSize
        self.startFrame              = reader.startFrame
        self.endFrame                = reader.endFrame
        self.baseline                = reader.baseline                [:,hnIndex,...]
        self.baselineCovariance      = reader.baselineCovariance      [:,hnIndex,...]

        self.converged               = reader.converged               [:,hnIndex]
        self.iterations              = reader.iterations              [:,hnIndex]
        self.confidenceScore         = reader.confidenceScore         [:,hnIndex]
        self.loglikelihood           = reader.loglikelihood           [:,hnIndex]
        self.deltaLoglikelihood      = reader.deltaLoglikelihood      [:,hnIndex]

        self.rawMean                 = reader.rawMean                 [:,hnIndex,...]
        self.rawCovariance           = reader.rawCovariance           [:,hnIndex,...]
        self.rawMixtureFraction      = reader.rawMixtureFraction      [:,hnIndex,...]

        self.smoothedMean            = reader.smoothedMean            [:,hnIndex,...]
        self.smoothedCovariance      = reader.smoothedCovariance      [:,hnIndex,...]
        self.smoothedMixtureFraction = reader.smoothedMixtureFraction [:,hnIndex,...]


class DmeDumpHoleNumberAndBlockSlice(object):
    def __init__(self, reader, hn, block):
        self.reader = reader
        self.holeNumber = hn
        self.block = block
        hnIndex = reader.lookupHoleIndex(hn)

        self.blockSize               = reader.blockSize               [block]
        self.startFrame              = reader.startFrame              [block]
        self.endFrame                = reader.endFrame                [block]
        self.baseline                = reader.baseline                [block,hnIndex,...]
        self.baselineCovariance      = reader.baselineCovariance      [block,hnIndex,...]

        self.converged               = reader.converged               [block,hnIndex]
        self.iterations              = reader.iterations              [block,hnIndex]
        self.confidenceScore         = reader.confidenceScore         [block,hnIndex]
        self.loglikelihood           = reader.loglikelihood           [block,hnIndex]
        self.deltaLoglikelihood      = reader.deltaLoglikelihood      [block,hnIndex]

        self.rawMean                 = reader.rawMean                 [block,hnIndex,...]
        self.rawCovariance           = reader.rawCovariance           [block,hnIndex,...]
        self.rawMixtureFraction      = reader.rawMixtureFraction      [block,hnIndex,...]

        self.smoothedMean            = reader.smoothedMean            [block,hnIndex,...]
        self.smoothedCovariance      = reader.smoothedCovariance      [block,hnIndex,...]
        self.smoothedMixtureFraction = reader.smoothedMixtureFraction [block,hnIndex,...]
