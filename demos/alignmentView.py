import sys, numpy as np, pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from pbcore.io import CmpH5Reader

borderPen = pg.mkPen((255,255,255), width=1)
textColor = pg.mkColor(255, 255, 255)
redBrush = QtGui.QBrush(QtCore.Qt.red)
transparentRedBrush = QtGui.QBrush(QtGui.QColor(255, 0, 0, 50))
redPen = QtGui.QPen(QtCore.Qt.red)
monospaceFont = QtGui.QFont("Courier", 14)
fm = QtGui.QFontMetrics(monospaceFont)


class BasicAlignmentViewBox(pg.ViewBox):
    def __init__(self, alnTpl, alnRead, transcript, aStart, width=None):
        # TODO: Why on earth do we need this invertY business here
        pg.ViewBox.__init__(self, invertY=True, border=borderPen, enableMouse=False)

        self.ti = QtGui.QGraphicsTextItem()
        self.ti.setDefaultTextColor(textColor)
        self.ti.setFont(monospaceFont)
        self.margin = self.ti.document().documentMargin()
        self.charWidth = fm.averageCharWidth()
        self.textHeight = 3 * fm.lineSpacing()
        self.tightTextHeight = 2 * fm.lineSpacing() + fm.ascent()

        self.setAlignment(alnTpl, alnRead, transcript, aStart)


        self.disableAutoRange(pg.ViewBox.XYAxes)
        self.setFixedHeight(self.ti.boundingRect().height())
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


    def setAlignment(self, tpl, read, transcript, aStart):
        print aStart
        self.alnTpl = tpl
        self.alnRead = read
        self.transcript = transcript
        self.aStart = aStart
        self.text = self.alnTpl + "\n" + self.transcript + "\n" + self.alnRead
        self.ti.setPlainText(self.text)

    def center(self, aMid):
        xCenter = self.margin + aMid * self.charWidth
        width = self.width()
        xStart = xCenter - width / 2.0
        xEnd = xCenter + width / 2.0
        self.setXRange(xStart, xEnd, padding=0)

    def highlightRange(self, aStart, aEnd):
        self.roiItem.setRegion((self.margin + aStart * self.charWidth,
                                self.margin + aEnd * self.charWidth))

    def focus(self, aStart, aEnd):
        aMid = float(aStart + aEnd) / 2
        self.highlightRange(aStart, aEnd)
        self.center(aMid)


class AlignmentViewBox(BasicAlignmentViewBox):
    """
    This class extents BasicAlignmentViewBox with the ability to grab
    the data from cmp.h5/BAM records
    """
    @staticmethod
    def fromSingleAlignment(alnHit, **kwargs):
        return AlignmentViewBox(alnHit.reference (orientation="native", aligned=True),
                                alnHit.read      (orientation="native", aligned=True),
                                alnHit.transcript(orientation="native", style="exonerate+"),
                                alnHit.aStart,
                                **kwargs)

    @staticmethod
    def fromAllAlignmentsInZmw(basZmwRead, alnHits):
        pass



class Main(object):

    def run(self):
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

        self.startSpinBox.valueChanged.connect(self.update)
        self.widthSpinBox.valueChanged.connect(self.update)

        self.groupBox.setLayout(self.groupBoxLayout)
        self.groupBoxLayout.addWidget(self.startSpinBox)
        self.groupBoxLayout.addWidget(self.widthSpinBox)

        l.addWidget(self.widget1)
        l.addWidget(self.groupBox)

        alnFname = sys.argv[1]
        rowNumber = int(sys.argv[2])
        alnF = CmpH5Reader(alnFname)
        aln = alnF[rowNumber]

        self.av = AlignmentViewBox.fromSingleAlignment(aln, width=740)
        self.av.setPos(20,20)
        self.widget1.addItem(self.av)

        self.update(None)
        self.win.show()

    def update(self, arg):
        # ignore arg
        aStart = self.startSpinBox.value()
        aEnd = aStart + self.widthSpinBox.value()
        self.av.focus(aStart, aEnd)

m = Main()
m.run()

import ipdb
ipdb.set_trace()
