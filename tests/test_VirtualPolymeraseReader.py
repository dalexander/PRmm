from PRmm.io import VirtualPolymeraseBamReader
from pbcore.io import BasH5Reader
from pbcore.data import getUnalignedBam, getBaxForBam
from pbcore.io.align._BamSupport import downsampleFrames

from numpy.testing import (assert_array_almost_equal as ASIM,
                           assert_array_equal        as AEQ)

from nose.tools import (nottest,
                        assert_raises,
                        assert_equal as EQ,
                        assert_almost_equal as EQISH)



class TestVirtualPolymeraseReader(object):

    def __init__(self):
        self.V = VirtualPolymeraseBamReader(getUnalignedBam())
        self.B = BasH5Reader(getBaxForBam())

    def test_basecalls(self):
        vpBasecalls = self.V[1650].basecalls()
        baxBasecalls = self.B[1650].readNoQC().basecalls()
        EQ(baxBasecalls, vpBasecalls)

    def test_preBaseFrames(self):
        vxPBF = self.V[1650].preBaseFrames()
        baxPBF = self.B[1650].readNoQC().IPD()
        # This will be equivalent up to the lossy encoding scheme of the kinetics
        AEQ(downsampleFrames(baxPBF), vxPBF)
