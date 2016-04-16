
__all__ = [ "ZmwReadStitcher" ]

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
FeatureDesc = \
    namedtuple("FeatureDesc",
               ("accessorName", "nameInManifest", "tagName", "decoder", "encodedDtype", "decodedDtype"))


FEATURE_DESCS = \
[   # Base features
    FeatureDesc("preBaseFrames"     , "Ipd:Frames"        , "ip", "identity", np.uint16, np.uint16),
    FeatureDesc("preBaseFrames"     , "Ipd:CodecV1"       , "ip", "codecV1",  np.uint8,  np.uint16),
    FeatureDesc("baseWidthFrames"   , "PulseWidth:Frames" , "pw", "identity", np.uint16, np.uint16),
    FeatureDesc("baseWidthFrames"   , "PulseWidth:CodecV1", "pw", "codecV1",  np.uint8,  np.uint16),
    # Pulse features
    FeatureDesc("startFrame"        , "StartFrame"        , "sf", "identity", np.uint32, np.uint32),
    FeatureDesc("pulseWidthFrames"  , "PulseCallWidth"    , "px", "identity", np.uint16, np.uint16),
    FeatureDesc("prePulseFrames"    , "PrePulseFrames"    , "pd", "identity", np.uint16, np.uint16)
 ]

_possibleFeatureManifestNames = set([ pd.nameInManifest
                                      for pd in FEATURE_DESCS ])

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


class ZmwReadStitcher(object):
    """
    A reader class that enables viewing the read records corresponding
    to a given ZMW, as present in a paired subreads.bam and
    scraps.bam, as if they were a contiguous ZMW read record.
    """
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
    def filename(self):
        return self.subreadsF.filename

    @property
    def hasPulseFeatures(self):
        return (self.subreadsF.hasPulseFeatures() and
                self.scrapsF.hasPulseFeatures())

    @property
    @cached
    def sequencingZmws(self):
        """
        Hole numbers for which we have basecalls and an HQ region
        """
        return sorted(set(self.subreadsF.holeNumber))

    @property
    @cached
    def allSequencingZmws(self):
        """
        Hole numbers for which we have basecalls
        """
        return sorted(set.union(set(self.subreadsF.holeNumber),
                                set(self.scrapsF.holeNumber)))

    def __getitem__(self, holeNumber):
        if holeNumber not in self.allSequencingZmws:
            raise IndexError, "Requested hole number has no entry in this BAM file"
        subreads = self.subreadsF.readsByHoleNumber(holeNumber)
        scraps = self.scrapsF.readsByHoleNumber(holeNumber)
        combined = sorted(subreads + scraps, key=lambda x: x.qStart)
        return StitchedZmw(self, combined)

    @property
    @cached
    def featureDescs(self):
      rgs = self.subreadsF.peer.header["RG"]
      assert len(rgs) == 1
      rg = rgs[0]
      dsEntries = set(pair.split("=")[0]
                      for pair in rg["DS"].split(";"))
      manifestNames = dsEntries.intersection(_possibleFeatureManifestNames)
      return { desc.accessorName : desc
               for desc in FEATURE_DESCS
               if desc.nameInManifest in manifestNames }

    @property
    @cached
    def frameRate(self):
        return self.subreadsF.readGroupTable[0].FrameRate

    @property
    @cached
    def movieName(self):
        mns = list(self.subreadsF.movieNames)
        assert len(mns) == 1
        return mns[0]


def _recordsFormReadPartition(records):
    """
    check that the records are contiguous in read space, starting at 0,
    and are from the same hole
    """
    qEnd = 0
    for r in records:
        if r.qStart != qEnd: return False
        qEnd = r.qEnd
    # passed first test...
    return len(set(r.HoleNumber for r in records)) == 1


def _concatenateRecordArrayTags(tag, dtype, records):
    parts = [ np.array(r.peer.get_tag(tag), dtype=dtype)
              for r in records ]
    return np.hstack(parts)

def _concatenateRecordStringTags(tag, records):
    return "".join(r.peer.get_tag(tag)
                   for r in records)

def _preciseReadType(bamRecord):
    readType = bamRecord.readType
    if readType == "SCRAP":
        scrapDetail = ":%s" % bamRecord.scrapType
    else:
        scrapDetail = ""
    return readType + scrapDetail


def _computePulseIndex(pc):
    """
    Returns an array the size of the *basecalls* (|uppercase letters in pc|);
    each entry encodes the index in pc of that basecall.
    """
    # np.char.islower is too slow AFAICT...
    isUpper = np.fromstring(pc, dtype=np.uint8) <= ord("Z")
    return np.flatnonzero(isUpper)


class StitchedZmw(BaseRegionsMixin):

    def __init__(self, reader, bamRecords):
        if not _recordsFormReadPartition(bamRecords):
            raise Exception, "Records do not form a contiguous span of a ZMW!"
        self.reader = reader
        self.holeNumber = bamRecords[0].HoleNumber
        self.bamRecords = bamRecords

    @property
    def zmwName(self):
      return "%s/%d" % (self.reader.movieName,
                        self.holeNumber)

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__,
                             self.zmwName)

    @property
    @cached
    def _features(self):
        """
        The assembled base and pulse features, as a dict
        """
        _features = { "basecalls" : "".join(r.peer.seq for r in self.bamRecords) }
        for featureName in self.reader.featureDescs:
            desc = self.reader.featureDescs[featureName]
            decode = Decoders.byName(desc.decoder)
            cat = _concatenateRecordArrayTags(desc.tagName, desc.encodedDtype, self.bamRecords)
            decoded = decode(cat)
            _features[featureName] = decoded

        # If we have pulse features, we need to add the pulsecalls and
        # an artificial feature for the "pulse index"
        if self.reader.hasPulseFeatures:
            pc = "".join(r.peer.get_tag("pc") for r in self.bamRecords)
            _features["pulsecalls"] = pc
            _features["pulseIndex"] = _computePulseIndex(pc)

        return _features

    @property
    def hasPulseFeatures(self):
        return "pulsecalls" in self._features

    @property
    @cached
    def zmwReadLength(self):
        return max(r.qEnd for r in self.bamRecords)

    def readNoQC(self, qStart=None, qEnd=None):
        """
        ... ref to bash5 method doc
        """
        if qEnd is None and qStart is not None:
            raise ValueError, "Must specify both args, or neither"
        if qStart is None:
            qStart, qEnd = 0, self.zmwReadLength
        return StitchedZmwRead(self, qStart, qEnd)

    def pulses(self):
        return self.readNoQC()

    @property
    def pulseIndex(self):
        return self._features["pulseIndex"]

    def read(self, qStart=None, qEnd=None):
        """
        ... ref to bash5 method doc
        """
        if qEnd is None and qStart is not None:
            raise ValueError, "Must specify both args, or neither"
        if qStart is None:
            qStart, qEnd = self.hqRegion
        else:
            qStart = max(qStart, self.hqRegion[0])
            qEnd   = min(qEnd, self.hqRegion[1])
        return StitchedZmwRead(self, qStart, qEnd)


    @property
    @cached
    def regionTable(self):
        """
        Get the "region table", a table indicating
        *base*-coordinate-delimited regions, using the same recarray
        dtype that is returned by BasH5Reader.

        *Note* that the regiontable from the StitchedZmwRead will
        not in general be equivalent to that from a bas.h5, if the BAM
        files were produced using bax2bam, because in our BAM
        encodings, a subread or adapter cannot extend beyond the HQ
        region.  Additionally there is no concept of a "region score"
        for the BAM.
        """
        zmwReadExtent = Interval(0, self.zmwReadLength)
        intervalsByType = defaultdict(list)
        for r in self.bamRecords:
            intervalsByType[_preciseReadType(r)].append(Interval(r.qStart, r.qEnd))

        # Find an HQ region
        hqIntervalTree = IntervalTree([zmwReadExtent])
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

    @property
    def hqRegionSnr(self):
        return self.bamRecords[0].hqRegionSnr



class StitchedZmwRead(object):

    # slots

    def __init__(self, zmw, qStart, qEnd):
        self.zmw = zmw
        self.qStart = qStart
        self.qEnd = qEnd
        # Pulse start, end?  Reckon these from pulseIndex
        if self.zmw.hasPulseFeatures:
            self.pStart = self.zmw.pulseIndex[self.qStart]
            if self.qEnd > self.qStart:
                self.pEnd   = self.zmw.pulseIndex[self.qEnd-1] + 1
            else:
                self.pEnd = self.pStart

    # Generic accessors

    def baseFeature(self, name):
        return self.zmw._features[name][self.qStart:self.qEnd]

    def pulseFeature(self, name):
        return self.zmw._features[name][self.pStart:self.pEnd]

    # Specific base feature accessors

    def basecalls(self):
        return self.baseFeature("basecalls")

    def preBaseFrames(self):
        return self.baseFeature("preBaseFrames")

    # Specific pulse feature accessors

    def pulsecalls(self):
        return self.pulseFeature("pulsecalls")

    def pulseIndex(self):
        return self.pulseFeature("pulseIndex")

    def PulseIndex(self):
        return self.pulseIndex()

    def pulseStartFrame(self):
        return self.pulseFeature("startFrame")

    def pulseWidthFrames(self):
        return self.pulseFeature("pulseWidthFrames")

    def prePulseFrames(self):
        return self.pulseFeature("prePulseFrames")

    def channel(self):
        # FIXME: get rid of this, make PRmm not have to know "channel"
        # anywhere, it's not useful.  Work off of pulse label.
        baseMap = "TGCA" # Sequel assumption...
        channelMap = np.zeros(shape=256, dtype=int)
        for c, b in enumerate(baseMap):
            channelMap[ord(b)] = c
        return channelMap[np.fromstring(self.pulsecalls(), dtype=np.uint8)]

    def channelBases(self):
        return self.pulsecalls()

    def pulseEndFrame(self):
        return self.pulseStartFrame() + self.pulseWidthFrames()


    # Other stuff

    @property
    def readName(self):
        return "%s/%d_%d" % (self.zmw.zmwName,
                             self.readStart,
                             self.readEnd)

    @property
    def readStart(self):
        return self.qStart

    @property
    def readEnd(self):
        return self.qEnd

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__,
                             self.readName)

    def __len__(self):
        return self.readEnd - self.readStart
