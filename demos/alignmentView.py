import sys, numpy as np, pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from pbcore.io import CmpH5Reader

borderPen = pg.mkPen((255,255,255), width=1)
textColor = pg.mkColor(255, 255, 255)
redBrush = QtGui.QBrush(QtCore.Qt.red)
monospaceFont = QtGui.QFont("Courier", 14)
fm = QtGui.QFontMetrics(monospaceFont)


class AlignmentViewBox(pg.ViewBox):
    def __init__(self, alnTpl, transcript, alnRead,
                 width=None, rStart=0):
        # TODO: Why on earth do we need this invertY business here
        pg.ViewBox.__init__(self, invertY=True, border=borderPen, enableMouse=False)

        self.alnTpl = alnTpl
        self.transcript = transcript
        self.alnRead = alnRead
        self.rStart = rStart

        text = alnTpl + "\n" + transcript + "\n" + alnRead
        html = "<html><head/><body>%s</body></html>" % text

        self.text = text
        self.ti = QtGui.QGraphicsTextItem(text)
        self.ti.setDefaultTextColor(textColor)
        self.ti.setFont(monospaceFont)
        self.margin = self.ti.document().documentMargin()
        self.charWidth = fm.averageCharWidth()
        self.textHeight = 3 * fm.lineSpacing()
        self.tightTextHeight = 2 * fm.lineSpacing() + fm.ascent()

        self.disableAutoRange(pg.ViewBox.XYAxes)
        self.setFixedHeight(self.ti.boundingRect().height())
        if width is not None:
            self.setFixedWidth(width)
        self.setRange(yRange=(0, self.boundingRect().height()), padding=0)
        self.setAspectLocked()
        self.addItem(self.ti)

        #self.addItem(pg.GridItem())

        self.rectItem = QtGui.QGraphicsRectItem(self.margin, self.margin,
                                                self.charWidth * 5, self.tightTextHeight)
        self.rectItem.setBrush(redBrush)
        self.rectItem.setZValue(-1)
        self.addItem(self.rectItem)


    def center(self, xCenter):
        width = self.width()
        xStart = xCenter - width / 2.0
        xEnd = xCenter + width / 2.0
        self.setXRange(xStart, xEnd, padding=0)


    def highlightRange(self, rStart, rEnd):
        # 1. Identify corresponding xrange
        # 2. Scroll the box horizontally to center on the range
        # 3. draw a rectangle or "ROI box" around the selected interval to
        #    highlight it.

        # self.setRange(xRange=(min, max))
        if rEnd < rStart:
            rEnd = rStart
        self.rectItem.setRect(self.margin + rStart * self.charWidth, self.margin,
                              self.charWidth * (rEnd - rStart), self.tightTextHeight)

        midChar = float(rStart + rEnd) / 2
        self.center(self.margin + midChar * self.charWidth)

app = QtGui.QApplication([])
win = QtGui.QMainWindow()
win.resize(800, 600)
win.setWindowTitle("Alignment View")

cw = QtGui.QWidget()
win.setCentralWidget(cw)
l = QtGui.QVBoxLayout()
cw.setLayout(l)


line1 = "FOO"*40+"WUT"+"FOO"*20
line2 = "|"*61*3
line3 = "BAR"*61
av = AlignmentViewBox(line1, line2, line3, width=740)
av.setPos(20, 20)


def update(arg):
    # ignore arg
    left = startSpinBox.value()
    right = endSpinBox.value()
    av.highlightRange(left, right)

widget1 = pg.GraphicsView()
groupBox = QtGui.QGroupBox()
startSpinBox = QtGui.QSpinBox()
endSpinBox = QtGui.QSpinBox()
groupBoxLayout = QtGui.QVBoxLayout()
startSpinBox.valueChanged.connect(update)
endSpinBox.valueChanged.connect(update)

groupBox.setLayout(groupBoxLayout)
groupBoxLayout.addWidget(startSpinBox)
groupBoxLayout.addWidget(endSpinBox)


l.addWidget(widget1)
l.addWidget(groupBox)


widget1.addItem(av)


win.show()



#v = w.addViewBox(invertY=True)




# def debug_trace():
#     # http://stackoverflow.com/questions/1736015/debugging-a-pyqt4-app
#     from ipdb import set_trace
#     QtCore.pyqtRemoveInputHook()
#     set_trace()


import ipdb
ipdb.set_trace()



# make a class for the alignment box---
# a viewbox containing the alignment, which is
# - not scalable, not draggable
# - can be scrolled by API




def main():
    # alnFname = sys.argv[1]
    # rowNumber = int(sys.argv[2])
    # alnF = CmpH5Reader(alnFname)
    # aln = alnF[rowNumber]
    pass

if __name__ == '__main__':
    main()
    app.exec_()


# TODO1: Set the viewbox to be same height as bounding box of the textitem
# TODO2: scroll it to the "WUT"
