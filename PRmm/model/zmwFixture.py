import numpy as np
from functools import wraps

from PRmm.model import Region

def cached(f):
    """
    Decorator that lets us memoize the return value of a nullary
    function call in an object-local cache.
    """
    @wraps(f)
    def g(self):
        if not hasattr(self, "_cache"):
            self._cache = {}
        if f.__name__ not in self._cache:
            self._cache[f.__name__] = f(self)
        else:
            print "Cache hit!"
        return self._cache[f.__name__]
    return g

class Unimplemented(Exception): pass

class ZmwFixture(object):
    """
    A ZMW fixture provides a ZMW level view of the world---access to
    data from a single ZMW, collating the different data types (trace,
    pulse, base, alignment).

    It provides a facade over the different BAM/HDF5 data files that
    might be providing base, pulse, and alignment data.  While
    minimal, this facade is sufficient for PRmm's purposes.
    """
    def __init__(self, readersFixture, holeNumber):
        self.readers = readersFixture
        self.holeNumber = holeNumber
        self._plsZmw = self.readers.plsF[holeNumber] if self.readers.hasPulses else None
        self._basZmw = self.readers.basF[holeNumber] if self.readers.hasBases  else None
        if self.readers.hasAlignments:
            self._alnsZmw = self.readers.alnF.readsByHoleNumber(holeNumber)
        else:
            self._alnsZmw = []

        # Cache this stuff:

        #     self.basStartFrame = self.basZmw.readNoQC().StartFrame()
        #     self.basEndFrame = self.basZmw.readNoQC().EndFrame()



    # -- Identifying info --

    @property
    def zmwName(self):
        return "%s/%d" % (self.readers.movieName, self.holeNumber)

    # -- Trace info --

    @property
    def cameraTrace(self):
        return self.readers.trcF[self.holeNumber]

    @property
    def dwsTrace(self):
        raise Unimplemented()

    # -- Pulsecall info --

    @property
    def hasPulses(self):
        return self._plsZmw is not None

    @property
    def pulses(self):
        pass

    @property
    def pulseFrameStart(self):
        pass

    @property
    def pulseFrameEnd(self):
        pass

    # -- Basecall info --

    @property
    def hasBases(self):
        return self._basZmw is not None

    @property
    def bases(self):
        pass

    @property
    def baseFrameStart(self):
        pass

    @property
    def baseFrameEnd(self):
        pass

    # signal intensity...

    # -- Alignment info ---

    @property
    def hasAlignments(self):
        return bool(self._alnsZmw)

    @property
    def multiAlignment(self):
        # returns (ref, transcriptEx+, read) :: (str, str, str),
        # where read represents the entire polymerase read
        raise Unimplemented()


    # -- Regions info --

    @property
    def regions(self):
        # Fix this code, it was just transplanted
        if self.basZmw is not None:
            basRead = self.basZmw.readNoQC()
            endFrames = np.cumsum(basRead.PreBaseFrames() + basRead.WidthInFrames())
            startFrames = endFrames - basRead.PreBaseFrames()
            for basRegion in basZmw.regionTable:
                startFrame = startFrames[basRegion.regionStart]
                endFrame = endFrames[basRegion.regionEnd-1] # TODO: check this logic
                yield Region(basRegion.regionType, startFrame, endFrame, "")
            # Are there alignments?
            if alns:
                for aln in alns:
                    yield Region(Region.ALIGNMENT_REGION,
                                 startFrames[aln.rStart],
                                 endFrames[aln.rEnd-1], "")


    # -- Interval queries --
