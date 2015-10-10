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
    def __init__(self, alnTpl, alnRead, transcript,
                 width=None, aStart=0):
        # TODO: Why on earth do we need this invertY business here
        pg.ViewBox.__init__(self, invertY=True, border=borderPen, enableMouse=False)

        self.ti = QtGui.QGraphicsTextItem()
        self.ti.setDefaultTextColor(textColor)
        self.ti.setFont(monospaceFont)
        self.margin = self.ti.document().documentMargin()
        self.charWidth = fm.averageCharWidth()
        self.textHeight = 3 * fm.lineSpacing()
        self.tightTextHeight = 2 * fm.lineSpacing() + fm.ascent()

        self.setAlignment(alnTpl, alnRead, transcript, aStart=aStart)


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


    def setAlignment(self, tpl, read, transcript, aStart=0):
        self.alnTpl = tpl
        self.alnRead = read
        self.transcript = transcript
        self.aStart = aStart
        self.text = self.alnTpl + "\n" + self.transcript + "\n" + self.alnRead
        self.ti.setPlainText(self.text)

    def center(self, rMid):
        xCenter = self.margin + rMid * self.charWidth
        width = self.width()
        xStart = xCenter - width / 2.0
        xEnd = xCenter + width / 2.0
        self.setXRange(xStart, xEnd, padding=0)

    def highlightRange(self, aStart, rEnd):
        self.roiItem.setRegion((self.margin + aStart * self.charWidth,
                                self.margin + rEnd * self.charWidth))

    def focus(self, aStart, rEnd):
        rMid = float(aStart + rEnd) / 2
        av.highlightRange(aStart, rEnd)
        av.center(rMid)


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
                                aStart=alnHit.aStart,
                                **kwargs)

    @staticmethod
    def fromAllAlignmentsInZmw(basZmwRead, alnHits):
        pass



app = QtGui.QApplication([])
win = QtGui.QMainWindow()
win.resize(800, 600)
win.setWindowTitle("Alignment View")

cw = QtGui.QWidget()
win.setCentralWidget(cw)
l = QtGui.QVBoxLayout()
cw.setLayout(l)


def update(arg):
    # ignore arg
    aStart = startSpinBox.value()
    rEnd = aStart + widthSpinBox.value()
    av.focus(aStart, rEnd)

widget1 = pg.GraphicsView()
groupBox = QtGui.QGroupBox()
startSpinBox = QtGui.QSpinBox()
widthSpinBox = QtGui.QSpinBox()
groupBoxLayout = QtGui.QVBoxLayout()
startSpinBox.valueChanged.connect(update)
widthSpinBox.valueChanged.connect(update)

groupBox.setLayout(groupBoxLayout)
groupBoxLayout.addWidget(startSpinBox)
groupBoxLayout.addWidget(widthSpinBox)


l.addWidget(widget1)
l.addWidget(groupBox)


alnFname = sys.argv[1]
rowNumber = int(sys.argv[2])
alnF = CmpH5Reader(alnFname)
aln = alnF[rowNumber]
av = AlignmentViewBox.fromSingleAlignment(aln, width=740)
av.setPos(20,20)
widget1.addItem(av)

update(None)
win.show()



import ipdb
ipdb.set_trace()
