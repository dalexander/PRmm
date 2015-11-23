
__all__ = [ "VirtualPolymeraseBamReader" ]

# don't make this harder than it needs to be.  just supply the API needed by the model
# Not tuned for efficiency at all

from pbcore.io import IndexedBamReader

class VirtualPolymeraseBamReader(object):

    def __init__(self, subreadsFname, scrapsFname=None):
        if not subreadsFname.endswith(".subreads.bam"):
            raise Exception, "Expecting a subreads.bam"
        if scrapsFname is None:
            scrapsFname = subreadsFname.replace("subreads.bam", "scraps.bam")
        self.subreadsF = IndexedBamReader(subreadsFname)
        self.scrapsF   = IndexedBamReader(scrapsFname)
        if (len(self.subreadsF.movieNames) > 0 or
            self.scrapsF.movieNames != self.subreadsF.movieNames):
            raise Exception, "Requires single movie BAM file, and matching scraps"

    @property
    def hasPulses(self):
        pass

    @property
    def holeNumbers(self):
        return self.subreadsF.holeNumber

    def __getitem__(self, holeNumber):
        subreads = self.subreadsF.readsByHoleNumber(holeNumber)
        scraps = self.scrapsF.readsByHoleNumber(holeNumber)
        combined = sorted(subreads + scraps, key=lambda x: x.qStart)
        return VirtualPolymeraseZmw(combined)


def recordsFormReadPartition(records):
    """
    check that the records are contiguous in read space, starting at 0
    """
    qEnd = 0
    for r in records:
        if r.qStart != qEnd: return False
        qEnd = r.qEnd
    return True


def concatenateRecordArrayTags(tag, records):
    pass

def concatenateRecordStringTags(tag, records):
    val = ""
    for r in records:
        val = val + r.peer.get_tag(tag)
    return val


def concatenateRecordTags(tag, records):
    assert len(records) > 0
    if records
    for record in


class VirtualPolymeraseZmw(object):

    def __init__(self, bamRecords):
        if recordsFormReadPartition(bamRecords):
            raise Exception, "Records do not form a contiguous span of a ZMW!"
        self.bamRecords = bamRecords

    def readNoQC(self):
        return self




fname = "~/Data/pbcore/m140905_042212_sidney_c100564852550000001823085912221377_s1_X0.subreads.bam"
V = VirtualPolymeraseBamReader(fname)
