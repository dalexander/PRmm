from PRmm.io import VirtualPolymeraseBamReader
from pbcore.io import BasH5Reader
from pbcore.data import getUnalignedBam, getBaxForBam
from pbcore.io.align._BamSupport import downsampleFrames

from numpy.testing import (assert_array_almost_equal as ASIM,
                           assert_array_equal        as AEQ)
import numpy as np

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

    def testRead(self):
        BZR = self.BZ.read()
        VZR = self.VZ.read()
        EQ(BZR.basecalls(), VZR.basecalls())


# Mockup some bam records reflecting the internal "pulse BAM" spec
from mock import Mock
from pysam import AlignedSegment
from pbcore.io import BamAlignment
from PRmm.io.VirtualPolymeraseBamIO import VirtualPolymeraseZmw, PulseFeatureDesc

pulsePeer = AlignedSegment()
pulsePeer.is_unmapped=True
pulsePeer.seq = "GATTACAGATTACA"
pulsePeer.qname = "FakePulseRead"
tags = dict(
    RG="00000000",
    np=1,
    qs=0,
    qe=14,
    rq=0.80,
    sn=[2.0, 3.0, 5.0, 6.0],
    ip=[15]*14,
    pw=[16]*14,
    zm=42,
    cx=2,
    # Now, the pulse stuff
    pc = " GAgggTTACAcccGATaaaTACA",
    pa = [5]*23, #pkmean
    pm = [4]*23, #pkmid
    pd = [3]*23, #prePulseFrames
    px = [2]*23, #pulseWidthInFrames
    sf = range(3, 1000, 5)[:23] # startFrame
)
pulsePeer.set_tags(tags.items())

mockBamReader = Mock(
    readGroupInfo=lambda x: Mock(ID=0,
                                 MovieName="FakeMovie",
                                 ReadType="SUBREAD",
                                 SequencingChemistry="FakeChemistry",
                                 FrameRate=100.0))
bamRecord = BamAlignment(mockBamReader, pulsePeer)


mockVpReader = Mock(movieName="FakeMovie",
                    pulseFeatureDescs=
                     { "preBaseFrames"     : PulseFeatureDesc("preBaseFrames"     , "Ipd:Frames"        , "ip", "identity", np.uint16, np.uint16),
                       "baseWidthInFrames" : PulseFeatureDesc("baseWidthInFrames" , "PulseWidth:Frames" , "pw", "identity", np.uint16, np.uint16) })

vpZmw = VirtualPolymeraseZmw(mockVpReader, [bamRecord])
