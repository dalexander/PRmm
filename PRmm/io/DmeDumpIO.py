__all__ = [ "DmeDumpReader" ]

import h5py, numpy as np, os.path as op
from PRmm.model.utils import cached

class DmeDumpReader(object):

    # No "nice API" here yet.  Ideally would be nice to be able to
    # slice by either HN or block

    def __init__(self, fname):
        self.filename = op.abspath(op.expanduser(fname))
        self.file = h5py.File(self.filename, "r")

        self.holeNumber      = self.file["/HoleNumber"]
        self.blockSize       = self.file["/BlockSize"]
        self.startFrame      = self.file["/StartFrame"]
        self.endFrame        = self.file["/EndFrame"]
        self.baseline        = self.file["/BaselineMean"]
        self.mean            = self.file["/SmoothedEstimates/Mean"]
        self.covariance      = self.file["/SmoothedEstimates/Covariance"]
        self.mixtureFraction = self.file["SmoothedEstimates/MixtureFraction"]
