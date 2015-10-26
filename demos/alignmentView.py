import sys, numpy as np, pyqtgraph as pg
from bisect import bisect_right, bisect_left
from pyqtgraph.Qt import QtCore, QtGui
from pbcore.io import CmpH5Reader

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


class BasicAlignmentViewBox(pg.ViewBox):
    def __init__(self, alnTpl, alnRead, transcript, aPos, width=None):
        # TODO: Why on earth do we need this invertY business here
        pg.ViewBox.__init__(self, invertY=True, border=borderPen, enableMouse=False)

        self.ti = QtGui.QGraphicsTextItem()
        self.ti.setDefaultTextColor(textColor)
        self.ti.setFont(monospaceFont)
        self.margin = self.ti.document().documentMargin()
        self.charWidth = fm.averageCharWidth()
        self.textHeight = 3 * fm.lineSpacing()
        self.tightTextHeight = 2 * fm.lineSpacing() + fm.ascent()

        self.setAlignment(alnTpl, alnRead, transcript, aPos)


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


    def setAlignment(self, tpl, read, transcript, aPos):
        self.alnTpl = tpl
        self.alnRead = read
        self.transcript = transcript
        self.aPos = aPos
        self.text = self.alnTpl + "\n" + self.transcript + "\n" + self.alnRead
        self.ti.setPlainText(self.text)

    def charPos(self, aStart, aEnd):
        # returns cStart, cMid, cEnd---the character offsets into the
        # alignment corresponding to the given read positioins
        cStart = bisect_left(self.aPos, aStart)
        cEnd   = bisect_left(self.aPos, aEnd)
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
        #debug_trace()
        cStart, cMid, cEnd = self.charPos(aStart, aEnd)
        self.highlightRange(cStart, cEnd)
        self.center(cMid)


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
                                alnHit.readPositions(orientation="native"),
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


        self.groupBox.setLayout(self.groupBoxLayout)
        self.groupBoxLayout.addWidget(self.startSpinBox)
        self.groupBoxLayout.addWidget(self.widthSpinBox)

        l.addWidget(self.widget1)
        l.addWidget(self.groupBox)

        alnFname = sys.argv[1]
        rowNumber = int(sys.argv[2])
        alnF = CmpH5Reader(alnFname)
        aln = alnF[rowNumber]

        self.startSpinBox.setRange(0, 1000000)
        self.widthSpinBox.setRange(0, 1000000)
        self.startSpinBox.setValue(aln.aStart)

        self.av = AlignmentViewBox.fromSingleAlignment(aln, width=740)
        self.av.setPos(20, 20)
        self.widget1.addItem(self.av)

        self.startSpinBox.valueChanged.connect(self.update)
        self.widthSpinBox.valueChanged.connect(self.update)

        self.update(None)
        self.win.show()

    def update(self, arg):
        # ignore arg
        aStart = self.startSpinBox.value()
        aEnd = aStart + self.widthSpinBox.value()
        self.av.focus(aStart, aEnd)

m = Main()
m.run()
sys.exit(m.app.exec_())




#import ipdb; ipdb.set_trace()
