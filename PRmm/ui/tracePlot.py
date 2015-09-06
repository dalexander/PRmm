import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui


class CustomViewBox(pg.ViewBox):
    """
    CustomViewBox implements the following behavior:
      - prevents scaling or panning in the y direction
      - ?
    """
    def __init__(self):
        super(CustomViewBox, self).__init__()

    def scaleBy(self, s=None, center=None, x=None, y=None):
        return super(CustomViewBox, self).scaleBy([s[0], 1.0], center, x, y)

    def translateBy(self, t=None, x=None, y=None):
        return super(CustomViewBox, self).translateBy(t, x, 0)
