__all__ = [ "AlignmentViewBox" ]

import sys, numpy as np, pyqtgraph as pg
from bisect import bisect_right, bisect_left
from pyqtgraph.Qt import QtCore, QtGui
from PRmm.model import *


borderPen = pg.mkPen((255,255,255), width=1)
textColor = pg.mkColor(255, 255, 255)
redBrush = QtGui.QBrush(QtCore.Qt.red)
transparentRedBrush = QtGui.QBrush(QtGui.QColor(255, 0, 0, 50))
redPen = QtGui.QPen(QtCore.Qt.red)
monospaceFont = QtGui.QFont("Courier", 14)
fm = QtGui.QFontMetrics(monospaceFont)


def debug_trace():
    # http://stackoverflow.com/questions/1736015/debugging-a-pyqt4-app
    from ipdb import set_trace
    QtCore.pyqtRemoveInputHook()
    set_trace()


class AlignmentViewBox(pg.ViewBox):
    def __init__(self, width=None):
        # TODO: Why on earth do we need this invertY business here
        pg.ViewBox.__init__(self, invertY=True, border=borderPen, enableMouse=False)
        self.ti = QtGui.QGraphicsTextItem()
        self.ti.setDefaultTextColor(textColor)
        self.ti.setFont(monospaceFont)
        self.margin = self.ti.document().documentMargin()
        self.charWidth = fm.averageCharWidth()
        self.textHeight = 3 * fm.lineSpacing()
        self.tightTextHeight = 2 * fm.lineSpacing() + fm.ascent()

        self.disableAutoRange(pg.ViewBox.XYAxes)
        self.setFixedHeight(self.textHeight + fm.xHeight())  # This is a real hack.

        if width is not None:
            self.setFixedWidth(width)
        self.setRange(yRange=(0, self.boundingRect().height()), padding=0)
        self.setAspectLocked()
        self.addItem(self.ti)

        #self.addItem(pg.GridItem())
        self.roiItem = pg.LinearRegionItem(movable=False, brush=transparentRedBrush)
        for line in self.roiItem.lines:
            line.setPen(redPen)
        self.addItem(self.roiItem)
        self.multiAln = None

    def setAlignments(self, multiAln):
        self.multiAln = multiAln
        self.text = multiAln.reference + "\n" + multiAln.transcript + "\n" + multiAln.read
        self.ti.setPlainText(self.text)

    @property
    def isInitialized(self):
        return self.multiAln is not None

    def charPos(self, aStart, aEnd):
        # returns cStart, cMid, cEnd---the character offsets into the
        # alignment corresponding to the given read positioins
        cStart = bisect_left(self.multiAln.readPos, aStart)
        cEnd   = bisect_left(self.multiAln.readPos, aEnd)
        cMid   = float(cStart + cEnd) / 2
        return cStart, cMid, cEnd

    def center(self, cMid):
        xCenter = self.margin + cMid * self.charWidth
        width = self.width()
        xStart = xCenter - width / 2.0
        xEnd = xCenter + width / 2.0
        self.setXRange(xStart, xEnd, padding=0)

    def highlightRange(self, cStart, cEnd):
        self.roiItem.setRegion((self.margin + cStart * self.charWidth,
                                self.margin + cEnd * self.charWidth))

    def focus(self, aStart, aEnd):
        if self.isInitialized:
            self.aStart = aStart
            self.aEnd = aEnd
            cStart, cMid, cEnd = self.charPos(aStart, aEnd)
            self.highlightRange(cStart, cEnd)
            self.center(cMid)


class Main(object):

    def run(self, readers, holeNumber):
        self.app = QtGui.QApplication([])
        self.win = QtGui.QMainWindow()
        self.win.resize(800, 600)
        self.win.setWindowTitle("Alignment View")

        cw = QtGui.QWidget()
        self.win.setCentralWidget(cw)
        l = QtGui.QVBoxLayout()
        cw.setLayout(l)

        self.widget1 = pg.GraphicsView()
        self.groupBox = QtGui.QGroupBox()
        self.startSpinBox = QtGui.QSpinBox()
        self.widthSpinBox = QtGui.QSpinBox()
        self.groupBoxLayout = QtGui.QVBoxLayout()


        self.groupBox.setLayout(self.groupBoxLayout)
        self.groupBoxLayout.addWidget(self.startSpinBox)
        self.groupBoxLayout.addWidget(self.widthSpinBox)

        l.addWidget(self.widget1)
        l.addWidget(self.groupBox)

        self.startSpinBox.setRange(0, 1000000)
        self.widthSpinBox.setRange(0, 1000000)

        self.av = AlignmentViewBox(width=740)
        zmw = readers[holeNumber]
        self.startSpinBox.setValue(0)
        self.av.setAlignment(zmw.multiAlignment)
        self.av.setPos(20, 20)
        self.widget1.addItem(self.av)

        self.startSpinBox.valueChanged.connect(self.update)
        self.widthSpinBox.valueChanged.connect(self.update)

        self.update(None)
        self.win.show()

    def setAlignment(self, alnHit, aStart=None, aEnd=None):
        self.av.setAlignment(alnHit, aStart, aEnd)
        aStart = self.av.aStart
        aEnd = self.av.aEnd
        self.startSpinBox.setValue(aStart)
        self.widthSpinBox.setValue(aEnd - aStart)

    def update(self, arg):
        # ignore arg
        aStart = self.startSpinBox.value()
        aEnd = aStart + self.widthSpinBox.value()
        self.av.focus(aStart, aEnd)



if __name__ == "__main__":
    readers = Fixture.fromIniFile("~/.pacbio/data-fixtures.ini", "4C-lambda")
    holeNumber = 182
    m = Main()
    m.run(readers, holeNumber)

    import ipdb; ipdb.set_trace()


    sys.exit(m.app.exec_())
