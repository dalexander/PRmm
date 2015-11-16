
class Region(object):
    """
    A region, in *frame* coordinates

    TODO: move this logic under fixture!
    """
    # These agree with regions enum defined for bas/bax files
    ADAPTER_REGION = 0
    INSERT_REGION  = 1
    HQ_REGION      = 2
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
