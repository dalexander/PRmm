
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

    @staticmethod
    def fetchRegions(basZmw, alns=[]):
        if basZmw is not None:
            basRead = basZmw.readNoQC()
            endFrames = np.cumsum(basRead.PreBaseFrames() + basRead.WidthInFrames())
            startFrames = endFrames - basRead.PreBaseFrames()
            for basRegion in basZmw.regionTable:
                startFrame = startFrames[basRegion.regionStart]
                endFrame = endFrames[basRegion.regionEnd-1] # TODO: check this logic
                yield Region(basRegion.regionType, startFrame, endFrame, "")
            # Are there alignments?
            if alns:
                for aln in alns:
                    yield Region(Region.ALIGNMENT_REGION,
                                 startFrames[aln.rStart],
                                 endFrames[aln.rEnd-1], "")
