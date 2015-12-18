
__all__ = [ "VirtualPolymeraseBamReader" ]

# don't make this harder than it needs to be.  just supply the API needed by the model
# Not tuned for efficiency at all

from pbcore.io import IndexedBamReader
from pbcore.io.align._BamSupport import codeToFrames
from pbcore.model import BaseRegionsMixin

from PRmm.model.utils import cached
from PRmm.model import Region

import numpy as np
from intervaltree import Interval, IntervalTree
from collections import namedtuple, defaultdict



# This duplicates stuff we have already in pbcore.  Unify?
PulseFeatureDesc = \
    namedtuple("PulseFeatureDesc",
               ("accessorName", "nameInManifest", "tagName", "decoder", "encodedDtype", "decodedDtype"))


PULSE_FEATURE_DESCS = \
 [ PulseFeatureDesc("preBaseFrames"     , "Ipd:Frames"        , "ip", "identity", np.uint16, np.uint16),
   PulseFeatureDesc("preBaseFrames"     , "Ipd:CodecV1"       , "ip", "codecV1",  np.uint8,  np.uint16),
   PulseFeatureDesc("baseWidthInFrames" , "PulseWidth:Frames" , "pw", "identity", np.uint16, np.uint16),
   PulseFeatureDesc("baseWidthInFrames" , "PulseWidth:CodecV1", "pw", "codecV1",  np.uint8,  np.uint16) ]


_possibleFeatureManifestNames = set([ pd.nameInManifest
                                      for pd in PULSE_FEATURE_DESCS ])

def toRecArray(dtype, arr):
    return np.rec.array(arr, dtype=dtype).flatten()

REGION_TABLE_DTYPE = [("holeNumber",  np.int32),
                      ("regionType",  np.int32),
                      ("regionStart", np.int32),
                      ("regionEnd",   np.int32),
                      ("regionScore", np.int32) ]


class Decoders(object):
    @staticmethod
    def identity(x):
        return x

    @staticmethod
    def codecV1(x):
        return codeToFrames(x)

    @staticmethod
    def qv(x):
        return x - 33

    @staticmethod
    def byName(name):
      lookup = { "identity": Decoders.identity,
                 "codecV1" : Decoders.codecV1,
                 "qv"      : Decoders.qv }
      return lookup[name]


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
    @cached
    def holeNumbers(self):
        return sorted(set(self.subreadsF.holeNumber))

    def __getitem__(self, holeNumber):
        if holeNumber not in self.holeNumbers:
            raise IndexError, "Requested hole number has no entry in this BAM file"
        subreads = self.subreadsF.readsByHoleNumber(holeNumber)
        scraps = self.scrapsF.readsByHoleNumber(holeNumber)
        combined = sorted(subreads + scraps, key=lambda x: x.qStart)
        return VirtualPolymeraseZmw(self, combined)

    @property
    @cached
    def pulseFeatureDescs(self):
      rgs = self.subreadsF.peer.header["RG"]
      assert len(rgs) == 1
      rg = rgs[0]
      dsEntries = set(pair.split("=")[0]
                      for pair in rg["DS"].split(";"))
      manifestNames = dsEntries.intersection(_possibleFeatureManifestNames)
      return { desc.accessorName : desc
               for desc in PULSE_FEATURE_DESCS
               if desc.nameInManifest in manifestNames }

    @property
    @cached
    def frameRate(self):
        return self.subreadsF.readGroupTable[0].FrameRate


def recordsFormReadPartition(records):
    """
    check that the records are contiguous in read space, starting at 0
    """
    qEnd = 0
    for r in records:
        if r.qStart != qEnd: return False
        qEnd = r.qEnd
    return True


def concatenateRecordArrayTags(tag, dtype, records):
    parts = [ np.array(r.peer.get_tag(tag), dtype=dtype)
              for r in records ]
    return np.hstack(parts)

def concatenateRecordStringTags(tag, records):
    return "".join(r.peer.get_tag(tag)
                   for r in records)



def _preciseReadType(bamRecord):
    readType = bamRecord.readType
    if readType == "SCRAP":
        scrapDetail = ":%s" % bamRecord.scrapType
    else:
        scrapDetail = ""
    return readType + scrapDetail


class VirtualPolymeraseZmw(BaseRegionsMixin):

    def __init__(self, reader, bamRecords):
        if not recordsFormReadPartition(bamRecords):
            raise Exception, "Records do not form a contiguous span of a ZMW!"
        self.reader = reader
        self.bamRecords = bamRecords

    def __len__(self):
        return max(r.qEnd for r in self.bamRecords)

    @property
    def holeNumber(self):
        return self.bamRecords[0].holeNumber

    def readNoQC(self):
        raise NotImplementedError()

    def read(self):
        raise NotImplementedError()

    def basecalls(self):
        return "".join(r.peer.seq for r in self.bamRecords)

    def preBaseFrames(self):
        desc = self.reader.pulseFeatureDescs["preBaseFrames"]
        decode = Decoders.byName(desc.decoder)
        cat = concatenateRecordArrayTags(desc.tagName, desc.encodedDtype, self.bamRecords)
        decoded = decode(cat)
        return decoded

    @property
    def regionTable(self):
        """
        Get the "region table", a table indicating
        *base*-coordinate-delimited regions, using the same recarray
        dtype that is returned by BasH5Reader.

        *Note* that the regiontable from the VirtualPolymeraseZmw will
        not in general be equivalent to that from a bas.h5, if the BAM
        files were produced using bax2bam, because in our BAM
        encodings, a subread or adapter cannot extend beyond the HQ
        region.  Additionally there is no concept of a "region score"
        for the BAM.
        """
        polymeraseReadExtent = Interval(0, len(self))
        intervalsByType = defaultdict(list)
        for r in self.bamRecords:
            intervalsByType[_preciseReadType(r)].append(Interval(r.qStart, r.qEnd))

        # Find an HQ region
        hqIntervalTree = IntervalTree([polymeraseReadExtent])
        for lqInterval in intervalsByType["SCRAP:L"]:
            hqIntervalTree.chop(*lqInterval)
        hqIntervals = list(hqIntervalTree)
        assert len(hqIntervals) in (0, 1)
        if len(hqIntervals) == 0:
            hqInterval = Interval(0, 0)
        else:
            hqInterval = hqIntervals[0]
        hqRegion = (self.holeNumber, Region.HQ_REGION, hqInterval.begin, hqInterval.end, 0)

        # Adapters, barcodes, and inserts (and filtered inserts)
        regionTypeMap = { "SUBREAD" : Region.INSERT_REGION,
                          "SCRAP:A" : Region.ADAPTER_REGION,
                          "SCRAP:B" : Region.BARCODE_REGION,
                          "SCRAP:F" : Region.INSERT_REGION }

        regions = [ hqRegion ] + \
                  [ (self.holeNumber, regionTypeMap[code], interval.begin, interval.end, 0)
                    for code in regionTypeMap
                    for interval in intervalsByType[code] ]

        return toRecArray(REGION_TABLE_DTYPE, regions)
