import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui

class TraceViewBox(pg.ViewBox):
    """
    TraceViewBox implements the following behavior:
      - prevents scaling or panning in the y direction
    """
    def __init__(self):
        super(TraceViewBox, self).__init__()

    def scaleBy(self, s=None, center=None, x=None, y=None):
        return super(TraceViewBox, self).scaleBy([s[0], 1.0], center, x, y)

    def translateBy(self, t=None, x=None, y=None):
        return super(TraceViewBox, self).translateBy(t, x, 0)


class TracePlotItem(pg.PlotItem):
    """
    TracePlotItem implements the trace plotting, axes, and associated
    scrolling/zooming behaviors (via view box) and lets
    drawing/plotting clients draw on it.
    """
    def __init__(self, title=None):
        super(TracePlotItem, self).__init__(viewBox=TraceViewBox(), title=title)

    # -- Coordinates where drawing clients should draw things
    @property
    def pulseOverlayY(self):
        return 0

    @property
    def pulseLabelY(self):
        return 800

    @property
    def regionOverlayY(self):
        pass

    @property
    def hqRegionOverlayY(self):
        pass
