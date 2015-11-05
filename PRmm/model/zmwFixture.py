
class ZmwFixture(object):
    """
    A ZMW fixture provides access to data from a single ZMW, collating
    the different data types (trace, pulse, base, alignment).

    It provides a facade over the different BAM/HDF5 data files that
    might be providing base, pulse, and alignment data.  While
    minimal, this facade is sufficient for PRmm's purposes.
    """
    def __init__(self, readersFixture, holeNumber):
        pass

    # -- Trace info --

    def hasTrace(self):
        pass

    def cameraTrace(self):
        pass

    def dwsTrace(self):
        pass

    # -- Pulsecall info --

    def hasPulses(self):
        pass

    def pulses(self):
        pass

    def pulseFrameStart(self):
        pass

    def pulseFrameEnd(self):
        pass

    # -- Basecall info --

    def hasBases(self):
        pass

    def bases(self):
        pass

    def baseFrameStart(self):
        pass

    def baseFrameEnd(self):
        pass

    # signal intensity...

    # -- Alignment info ---

    def hasAlignments(self):
        pass

    def multiAlignment(self):
        # returns (ref, transcriptEx+, read) :: (str, str, str),
        # where read represents the entire polymerase read
        pass


    # -- Regions info --

    def regions(self):
        pass
