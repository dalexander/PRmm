import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui

from PRmm.io import BasecallsUnavailable

# TODO: move this somewhere else?
class Region(object):
    """
    A region, in *frame* coordinates
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
    def regionsFromBasZmw(basZmw):
        basRead = basZmw.readNoQC()
        endFrames = np.cumsum(basRead.PreBaseFrames() + basRead.WidthInFrames())
        startFrames = endFrames - basRead.PreBaseFrames()
        for basRegion in basZmw.regionTable:
            startFrame = startFrames[basRegion.regionStart]
            endFrame = endFrames[basRegion.regionEnd-1] # TODO: check this logic
            yield Region(basRegion.regionType, startFrame, endFrame, "")




class RegionsOverlayItem(pg.GraphicsObject):
    """
    Region display
    """
    pens = { Region.ADAPTER_REGION   : pg.mkPen(pg.mkColor(0,0,100), width=2),
             Region.INSERT_REGION    : pg.mkPen(pg.mkColor(0,100,0), width=2),
             Region.HQ_REGION        : pg.mkPen(pg.mkColor(100,0,0), width=2),
             Region.ALIGNMENT_REGION : pg.mkPen(pg.mkColor(100,100,0), width=2)  }

    def __init__(self, regions, plot):
        pg.GraphicsObject.__init__(self)
        self.plot = plot
        self.regions = regions
        self.generatePicture()

    @property
    def regionOverlayY(self):
        a, b = self.plot.visibleSpanY
        return a + (b - a) * 0.97

    @property
    def hqRegionOverlayY(self):
        a, b = self.plot.visibleSpanY
        return a + (b - a) * 1.00

    def generatePicture(self):
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        for region in self.regions:
            p.setPen(self.pens[region.regionType])
            if region.regionType == Region.HQ_REGION:
                y = self.hqRegionOverlayY
            else:
                y = self.regionOverlayY
            p.drawLine(QtCore.QPointF(region.startFrame, y),
                       QtCore.QPointF(region.endFrame, y))

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())



class PulsesOverlayItem(pg.GraphicsObject):
    """
    The pulses!
    """
    def __init__(self, plsZmw, plot):
        pg.GraphicsObject.__init__(self)
        self.plsZmw = plsZmw
        self.plot = plot
        self.generatePicture()
        self._textItems = []

    @property
    def pulseLabelY(self):
        a, b = self.plot.visibleSpanY
        return a + (b - a) * 0.84

    def generatePicture(self):
        # Precompute a QPicture object
        allPulses = self.plsZmw.pulses()
        startFrame    = allPulses.startFrame()
        widthInFrames = allPulses.widthInFrames()
        channel       = allPulses.channel()
        base          = allPulses.channelBases()

        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        pens  = [ pg.mkPen((i, 4), width=2) for i in xrange(4) ]
        y = -5
        for i in xrange(len(channel)):
            c     = channel[i]
            start = startFrame[i]
            width = widthInFrames[i]
            end = start + width
            p.setPen(pens[c])
            p.drawLine(QtCore.QPointF(start, y), QtCore.QPointF(start+width, y))

    def pulsesToLabel(self):
        """
        Returns None, or a ZmwPulses if we are focused on a small enough window for labeling
        """
        viewRange = self.plot.viewRange()[0]
        if viewRange[1] - viewRange[0] >= 500:
            return None
        pulsesToDraw = self.plsZmw.pulsesByFrameInterval(viewRange[0], viewRange[1])
        if len(pulsesToDraw) > 20:
            return None
        else:
            return pulsesToDraw

    def labelPulses(self, pulsesToLabel):
        # Remove the old labels from the scene
        for ti in self._textItems:
            ti.scene().removeItem(ti)
        self._textItems = []

        if pulsesToLabel is None: return

        start      = pulsesToLabel.startFrame()
        width      = pulsesToLabel.widthInFrames()
        channel    = pulsesToLabel.channel()
        base       = pulsesToLabel.channelBases()
        mid        = start + width / 2.0
        try:
            isBase     = pulsesToLabel.isBase()
        except BasecallsUnavailable:
            isBase = np.ones_like(channel, dtype=bool)

        y = self.pulseLabelY
        for i in xrange(len(base)):
            pulseLabel = base[i] if isBase[i] else "-"
            ti = pg.TextItem(pulseLabel, anchor=(0.5, 0.5))
            ti.setParentItem(self)
            ti.setPos(mid[i], y)
            self._textItems.append(ti)

    def paint(self, p, *args):
        # Draw the pulse blips
        p.drawPicture(0, 0, self.picture)
        # Draw pulse labels if the focus is small enough (< 500 frames)
        self.labelPulses(self.pulsesToLabel())

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())
