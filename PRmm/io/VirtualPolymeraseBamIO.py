
__all__ = [ "VirtualPolymeraseBamReader" ]

# don't make this harder than it needs to be.  just supply the API needed by the model
# Not tuned for efficiency at all

from pbcore.io import IndexedBamReader
from pbcore.io.align._BamSupport import codeToFrames

from PRmm.model.utils import cached

import numpy as np
from collections import namedtuple



# This duplicates stuff we have already in pbcore.  Unify?
PulseFeatureDesc = namedtuple("PulseFeatureDesc",
                              ("accessorName", "nameInManifest", "tagName", "decoder", "encodedDtype", "decodedDtype"))


PULSE_FEATURE_DESCS = [ PulseFeatureDesc("preBaseFrames"     , "Ipd:Frames"        , "ip", "identity", np.uint16, np.uint16),
                        PulseFeatureDesc("preBaseFrames"     , "Ipd:CodecV1"       , "ip", "codecV1",  np.uint8,  np.uint16),
                        PulseFeatureDesc("baseWidthInFrames" , "PulseWidth:Frames" , "pw", "identity", np.uint16, np.uint16),
                        PulseFeatureDesc("baseWidthInFrames" , "PulseWidth:CodecV1", "pw", "codecV1",  np.uint8,  np.uint16) ]


_possibleFeatureManifestNames = set([ pd.nameInManifest
                                      for pd in PULSE_FEATURE_DESCS ])


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


class VirtualPolymeraseZmw(object):

    def __init__(self, reader, bamRecords):
        if not recordsFormReadPartition(bamRecords):
            raise Exception, "Records do not form a contiguous span of a ZMW!"
        self.reader = reader
        self.bamRecords = bamRecords

    def readNoQC(self):
        return self

    def basecalls(self):
        return "".join(r.peer.seq for r in self.bamRecords)

    def preBaseFrames(self):
        desc = self.reader.pulseFeatureDescs["preBaseFrames"]
        decode = Decoders.byName(desc.decoder)
        cat = concatenateRecordArrayTags(desc.tagName, desc.encodedDtype, self.bamRecords)
        decoded = decode(cat)
        return decoded


# def _makeFeatureAccessor(featureDesc):
#     def accessFeature(zmw):
#         return "here's your feature from ", featureDesc.nameInManifest

#     return property(accessFeature)

# for name in
#     setattr(VirtualPolymeraseZmw, name, 2)
