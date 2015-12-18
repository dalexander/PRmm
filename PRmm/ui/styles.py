from pyqtgraph import mkPen, mkColor

# The dicts returned by these objects are indexed by ...

class SequelStyle(object):

    @property
    def tracePens(self):
        return [ mkPen(mkColor("g"), width=1),
                 mkPen(mkColor("r"), width=1) ]

    @property
    def pulseOverlayPens(self):
        #       TGCA
        # Color ggrr
        # Ampl  2121
        return [ mkPen(mkColor("g"), width=4),
                 mkPen(mkColor("g"), width=2),
                 mkPen(mkColor("r"), width=4),
                 mkPen(mkColor("r"), width=2) ]

class RsStyle(object):

    # These are just arbitrary.  If we want, We could make it agree
    # with the physics, or with what PR shows.

    @property
    def tracePens(self):
        return [ mkPen(mkColor(i, 4), 1)
                 for i in xrange(4) ]

    @property
    def pulseOverlayPens(self):
        return [ mkPen(mkColor(i, 4), width=2)
                 for i in xrange(4) ]


def styleForData(fx):
    if fx.platform == "Sequel":
        return SequelStyle()
    else:
        return RsStyle()
