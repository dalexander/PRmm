


from pbcore.io import ReaderBase, readFofn
import h5py, os.path as op

class MultipartReader(object):
    """
    Abstract base class for multipart readers.  We also allow these to
    open "single part" files, since for example a "pls.h5" can be a
    single part old-style file, or the multipart stub file.
    """
    PART_READER_CLASS = None

    def __init__(self, fname, *rest):
        # Can read any of the following:
        #  ~ fofn
        #  ~ h5, multipart
        #  ~ h5, single part
        if fname.endswith(".h5"):
            directory = op.dirname(fname)
            with h5py.File(fname, "r") as f:
                if f.get("MultiPart"):
                    partFilenames = [ op.join(directory, fn)
                                      for fn in f["/MultiPart/Parts"] ]
                else:
                    partFilenames = [ fname ]
        elif fname.endswith(".fofn"):
            partFilenames = list(readFofn(fname))
        self._parts = [ self.PART_READER_CLASS(pfn, *rest)
                        for pfn in partFilenames ]

        # We don't even bother to create a "hole number map" for now.
        # The whole holenumber mapping business has always been a
        # mess, and X/Y encoding makes it even worse.  Building
        # another giant dictionary of boxed integers is not a great
        # plan.

    def _getitemScalar(self, hn):
        for part in self._parts:
            if hn in part: return part[hn]
        else:
            raise IndexError, "Hole number not found in any part"


    def __getitem__(self, holeNumbers):
        if (isinstance(holeNumbers, int) or
            issubclass(type(holeNumbers), np.integer)):
            return self._getitemScalar(holeNumbers)
        else:
            raise ValueError, "Only support for scalar slicing at present"


    def __enter__(self):
        return self

    def __exit__(self ,type, value, traceback):
        for part in self._parts:
            part.close()
        self._parts = None
