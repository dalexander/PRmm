
__all__ = [ "VirtualPolymeraseBamReader" ]

# don't make this harder than it needs to be.  just supply the API needed by the model

from pbcore.io import IndexedBamReader

def recordsStartAtZero():
    pass

def recordsAreContiguousReads():
    pass

def concatenateRecordTags():
    pass

class VirtualPolymeraseBamReader(object):

    def __init__(self, subreadsFname, scrapsFname=None):
        if not subreadsFname.endswith(".subreads.bam"):
            raise Exception, "Expecting a subreads.bam"
        if scrapsFname is None:
            scrapsFname = subreadsFname.replace("subreads.bam", "scraps.bam")
        self.subreadsF = IndexedBamReader(subreadsFname)
        self.scrapsF   = IndexedBamReader(scrapsFname)

    @property
    def hasPulses(self):
        pass

    @property
    def holeNumbers(self):
        return self.subreadsF.holeNumber

    def __getitem__(self, holenumber):
        pass


class VirtualPolymeraseZmw(object):

    def __init__(self, bamRecords):
        pass

    def readNoQC(self):
        return self
