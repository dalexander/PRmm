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
        self.VZ = self.V[1650]
        self.BZ = self.B[1650]

    def test_basecalls(self):
        vpBasecalls = self.VZ.readNoQC().basecalls()
        baxBasecalls = self.BZ.readNoQC().basecalls()
        EQ(baxBasecalls, vpBasecalls)

    def test_preBaseFrames(self):
        vpPBF = self.VZ.readNoQC().preBaseFrames()
        baxPBF = self.BZ.readNoQC().IPD()
        # This will be equivalent up to the lossy encoding scheme of the kinetics
        AEQ(downsampleFrames(baxPBF), vpPBF)

    def test_regionTable(self):
        # don't test the region table--they aren't equal.  but the
        # clipped-to-hq regions *are* equal
        AEQ(self.VZ.adapterRegions, self.BZ.adapterRegions)
        AEQ(self.VZ.insertRegions,  self.BZ.insertRegions)
        AEQ(self.VZ.hqRegion,       self.BZ.hqRegion)


    def test_regionTable_allZmws(self):
        for hn in self.B.allSequencingZmws:

            if hn == 49050:
                # hn 49050 exposes the fact that the way bax2bam works
                # does not respect the "insert" annotations in the
                # region table, it just takes the intervals within the
                # HQ region that fall between adapters.  This may or
                # not be the desired behavior... Lance had a reason
                # for doing it that way, I think based on the fact
                # that this was the way it was done in the C#
                # codebase, and it had some perceived advantage.
                # Maybe revisit that behavior.
                continue

            BZ = self.B[hn]
            VZ = self.V[hn]
            AEQ(BZ.adapterRegions, VZ.adapterRegions)
            AEQ(BZ.hqRegion, VZ.hqRegion)
            AEQ(BZ.insertRegions, VZ.insertRegions)
