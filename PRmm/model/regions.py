__all__ = [ "Region", "Regions" ]

class Region(object):
    """
    A region, in *frame* coordinates
    """
    # These agree with regions enum defined for bas/bax files
    ADAPTER_REGION = 0
    INSERT_REGION  = 1
    HQ_REGION      = 2

    # This is new.
    BARCODE_REGION = 3

    # This is new
    ALIGNMENT_REGION = 101

    typeNames = { ADAPTER_REGION   : "ADAPTER",
                  INSERT_REGION    : "INSERT",
                  HQ_REGION        : "HQ",
                  ALIGNMENT_REGION : "ALIGNMENT" }

    def __init__(self, regionType, startFrame, endFrame, name=""):
        self.regionType = regionType
        self.startFrame = startFrame
        self.endFrame   = endFrame
        self.name       = name

    def __repr__(self):
        return "<Region: %10s %7d %7d>" % (Region.typeNames[self.regionType],
                                         self.startFrame,
                                         self.endFrame)

    def __cmp__(self, other):
        return cmp((self.startFrame, self.regionType),
                   (other.startFrame, other.regionType))

    @property
    def frameExtent(self):
        return (self.startFrame, self.endFrame)


class Regions(object):
    """
    Convenient interface for the region list
    """
    def __init__(self, listOfRegion):
        self._regions = listOfRegion

    def __repr__(self):
        return repr(self._regions)

    def __iter__(self):
        return iter(self._regions)

    @property
    def all(self):
        return self._regions

    @property
    def alignment(self):
        alnRegions = [ r for r in self._regions
                       if r.regionType == Region.ALIGNMENT_REGION]
        if len(alnRegions) != 1:
            raise Exception, "Expecting a (single) alignment region!"
        return alnRegions[0]

    @property
    def alignments(self):
        return [ r for r in self._regions
                 if r.regionType == Region.ALIGNMENT_REGION ]

    @property
    def hqRegion(self):
        hqRegions = [ r for r in self._regions
                      if r.regionType == Region.HQ_REGION ]
        if len(hqRegions) != 1:
            raise Exception, "Expecting a (single) HQ region!"
        return hqRegions[0]

    @property
    def inserts(self):
        return [ r for r in self._regions
                 if r.regionType == Region.INSERT_REGION ]

    @property
    def adapters(self):
        return [ r for r in self._regions
                 if r.regionType == Region.ADAPTER_REGION ]
