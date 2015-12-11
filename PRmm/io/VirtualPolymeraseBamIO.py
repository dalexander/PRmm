
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
        if (len(self.subreadsF.movieNames) != 1 or
            self.scrapsF.movieNames != self.subreadsF.movieNames):
            raise Exception, "Requires single movie BAM file, and matching scraps"

    @property
    def hasPulses(self):
        pass

    @property
    def holeNumbers(self):
        return sorted(set(self.subreadsF.holeNumber))

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
    return "".join(r.peer.get_tag(tag)
                   for r in records)

def concatenatingRecordAccessor(tag, tagType):
    if tagType == "Z":
        pass
    else:
        raise Exception, "unimplemented"


class VirtualPolymeraseZmw(object):

    def __init__(self, bamRecords):
        if not recordsFormReadPartition(bamRecords):
            raise Exception, "Records do not form a contiguous span of a ZMW!"
        self.bamRecords = bamRecords

    def readNoQC(self):
        return self

    def basecalls(self):
        return "".join(r.peer.seq for r in self.bamRecords)
