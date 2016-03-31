import numpy as np
from bisect import bisect_left, bisect_right

from PRmm.model import Region, Regions, MultiAlignment
from PRmm.model.utils import cached

class Unimplemented(Exception): pass
class Unavailable(Exception): pass


class FixtureZmw(object):
    """
    A FixtureZmw provides a ZMW level view of the world---access to
    data from a single ZMW, collating the different data types (trace,
    pulse, base, alignment).

    It provides a facade over the different BAM/HDF5 data files that
    might be providing base, pulse, and alignment data.  While
    minimal, this facade is sufficient for PRmm's purposes.
    """
    def __init__(self, readersFixture, holeNumber):
        self.readers = readersFixture
        self.holeNumber = holeNumber


    @property
    @cached
    def _pulses(self):
        if self.readers.hasPulses:
            return self.readers.plsF[self.holeNumber].pulses()
        else:
            return None

    @property
    @cached
    def _bases(self):
        if self.readers.hasBases:
            return self.readers.basF[self.holeNumber].readNoQC()
        else:
            return None

    @property
    @cached
    def _alns(self):
        if self.readers.hasAlignments:
            return self.readers.alnF.readsByHoleNumber(self.holeNumber)
        else:
            return []


    # -- Identifying info --

    @property
    def zmwName(self):
        return "%s/%d" % (self.readers.movieName, self.holeNumber)

    @property
    def frameRate(self):
        return self.readers.frameRate

    @property
    def hqRegionSnr(self):
        return self.readers.basF[self.holeNumber].hqRegionSnr

    # -- Trace info --

    @property
    def cameraTrace(self):
        return self.readers.trcF[self.holeNumber]

    @property
    def dwsTrace(self):
        raise Unimplemented()

    @property
    def numFrames(self):
        return self.readers.trcF.numFrames


    # -- Pulsecall info --

    @property
    def hasPulses(self):
        return self.readers.hasPulses

    @property
    def numPulses(self):
        return len(self._pulses)

    @property
    def pulseChannel(self):
        return self._pulses.channel()

    @property
    def pulseLabel(self):
        return self._pulses.channelBases()

    @property
    def pulseStartFrame(self):
        return self._pulses.pulseStartFrame()

    @property
    def pulseEndFrame(self):
        return self._pulses.pulseEndFrame()

    @property
    def pulseWidth(self):
        return self._pulses.pulseWidthFrames()

    @property
    def prePulseFrames(self):
        return self._pulses.prePulseFrames()

    @property
    def pulsePkmid(self):
        return self._pulses.midSignal()

    @property
    def pulsePkmean(self):
        # We are returning just the "active channel" pkmean here;
        # pls.h5 files store all channels.
        return self._pulses.meanSignal()

    @property
    def pulseLabelQV(self):
        return self._pulses.labelQV()

    @property
    def pulseIsBase(self):
        ans = np.zeros(self.numPulses, dtype=bool)
        ans[self.basePulseIndex] = True
        return ans

    # -- Basecall info --

    @property
    def hasBases(self):
        return self.readers.hasBases

    @property
    def numBases(self):
        return len(self._bases)

    @property
    def baseLabel(self):
        return self._bases.basecalls()

    @property
    @cached
    def baseStartFrame(self):
        return self.pulseStartFrame[self.basePulseIndex]

    @property
    @cached
    def baseEndFrame(self):
        return self.pulseEndFrame[self.basePulseIndex]

    @property
    def basePulseIndex(self):
        return self._bases.PulseIndex()

    @property
    def baseWidthInFrames(self):
        pass

    @property
    def preBaseFrames(self):
        pass

    # -- Alignment info ---

    @property
    def hasAlignments(self):
        return bool(self._alns)

    @property
    def multiAlignment(self):
        return MultiAlignment.fromAlnHits(self.baseLabel, self._alns)

    @property
    def alignments(self):
        return self._alns

    @property
    def alignment(self):
        if len(self._alns) != 1:
            raise Exception, "Expecting a (single) alignment!"
        return self._alns[0]

    # -- Regions info --

    @property
    def hasBaseRegions(self):
        return self.hasBases


    @property
    @cached
    def baseRegions(self):
        """
        Get region info---BASE delimited
        """
        if not self.hasBases:
            raise Unavailable, "Bases are required to access regions"
        else:
            ans = []
            for basRegion in self._bases.zmw.regionTable:
                # FIXME: hacky workaround for bam2bax breakage
                if basRegion.regionStart == basRegion.regionEnd:
                    start = end = 0
                else:
                    start = basRegion.regionStart
                    end   = basRegion.regionEnd
                ans.append(Region(basRegion.regionType, start, end))
            # Are there alignments?
            if self.hasAlignments:
                for aln in self._alns:
                    ans.append(Region(Region.ALIGNMENT_REGION, aln.aStart, aln.aEnd))
            return Regions(sorted(ans))


    @property
    def hasTraceRegions(self):
        return self.hasBases and self.hasPulses

    @property
    @cached
    def traceRegions(self):
        """
        Get region info---FRAME delimited
        """
        if (not self.hasPulses or not self.hasBases):
            raise Unavailable, "Pulses and bases are required to access regions"
        else:
            baseRegions = self.baseRegions
            traceRegions = [ Region(br.regionType,
                                    self.baseStartFrame[br.start],
                                    self.baseEndFrame[max(br.end - 1, 0)])  # This logic is probably incorrect.
                             for br in baseRegions ]
            return Regions(traceRegions)



    # -- Interval queries --

    def baseIntervalFromFrames(self, frameStart, frameEnd):
        return (bisect_left (self.baseEndFrame,   frameStart),
                bisect_right(self.baseStartFrame, frameEnd))

    def pulseIntervalFromFrames(self, frameStart, frameEnd):
        return (bisect_left (self.pulseEndFrame,   frameStart),
                bisect_right(self.pulseStartFrame, frameEnd))
