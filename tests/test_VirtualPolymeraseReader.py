from PRmm.io import VirtualPolymeraseBamReader
from pbcore.io import BasH5Reader
from pbcore.data import getUnalignedBam, getBaxForBam

class TestVirtualPolymeraseReader(object):

    def __init__(self):
        self.V = VirtualPolymeraseBamReader(getUnalignedBam())
        self.B = BasH5Reader(getBaxForBam())

    def test_VirtualPolymeraseReader(self):
        vpBasecalls = self.V[1650].basecalls()
        baxBasecalls = self.B[1650].readNoQC().basecalls()
        assert baxBasecalls == vpBasecalls
