
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

    def __init__(self, regionType, startFrame, endFrame, name):
        self.regionType = regionType
        self.startFrame = startFrame
        self.endFrame   = endFrame
        self.name       = name
