__all__ = [ "MultiAlignment" ]

import numpy as np

class MultiAlignment(object):
    """
    not an MSA---this is the multiple alignments possibly present in a
    ZMWm unrolled.  Transcript is "exonerate+" formatted.
    """
    def __init__(self, reference, read, transcript, readPos):
        self.reference  = reference
        self.read       = read
        self.transcript = transcript
        self.readPos    = readPos

    @staticmethod
    def fromAlnHits(fullReadBasecalls, alnHits):
        sortedHits = sorted(alnHits, key=lambda h: h.aStart)

        iRefs    = []
        iReads   = []
        iScripts = []
        iReadPos = []

        def addAlignedInterval(hit):
            iRefs    .append(hit.reference (orientation="native", aligned=True))
            iReads   .append(hit.read      (orientation="native", aligned=True))
            iScripts .append(hit.transcript(orientation="native", style="exonerate+"))
            iReadPos .append(hit.readPositions(orientation="native"))

        def addUnalignedInterval(rStart, rEnd):
            iRefs    .append(" " * (rEnd-rStart))
            iReads   .append(fullReadBasecalls[rStart:rEnd])
            iScripts .append(" " * (rEnd-rStart))
            iReadPos .append(np.arange(rStart, rEnd, dtype=np.int))

        prevEnd = 0
        for hit in sortedHits:
            if hit.aStart > prevEnd:
                addUnalignedInterval(prevEnd, hit.aStart)
            addAlignedInterval(hit)
            prevEnd = hit.aEnd
        if prevEnd < len(fullReadBasecalls):
            addUnalignedInterval(hit.aEnd, len(fullReadBasecalls))

        return MultiAlignment(
            "".join(iRefs),
            "".join(iReads),
            "".join(iScripts),
            np.concatenate(iReadPos))
