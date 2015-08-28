import cffi, h5py, numpy as np
from pkg_resources import Requirement, resource_filename

def _getAbsPath(fname):
    return resource_filename(Requirement.parse("PRmm"), "%s" % fname)

class GbmModel(object):

    def __init__(self, filename, modelGroupName, nTrees=-1):
        self.name = filename + "::" + modelGroupName
        file = h5py.File(filename, "r")
        group = file[modelGroupName]
        self._loadNativeLib()
        self._loadModel(group)
        if nTrees == -1:
            self._nTrees = self._nTotalTrees
        else:
            self._nTrees = nTrees

    def _loadModel(self, group):

        def ds(name): return group[name][:]

        # deduce dimensions
        (self._nTotalTrees, self._treeSize) = ds("Variables").shape
        self._maxCSplits  = ds("CSplits").shape[1]

        # load arrays
        self._varNames     = ds("VarNames")     .flatten()
        self._varTypes     = ds("VarTypes")     .flatten()
        self._splitVar     = ds("Variables")    .flatten()
        self._leftNodes    = ds("LeftNodes")    .flatten()
        self._rightNodes   = ds("RightNodes")   .flatten()
        self._missingNodes = ds("MissingNodes") .flatten()
        self._splitCodes   = ds("SplitCodes")   .flatten() .astype(np.float32)
        self._cSplits      = ds("CSplits")      .flatten()
        self._initialValue = ds("InitialValue") .flatten() .astype(np.float32)[0]

        if "RelativeInfluence" in group:
            self._relativeInfluence = ds("RelativeInfluence")

    def _loadNativeLib(self):
        ffi = cffi.FFI()
        ffi.cdef("""
          void innerPredict(float radPredF[], float **dataMatrix, int cRows, int left[],
                            int right[], int missing[], float splitCode[], int splitVar[],
                            int cSplits[], int varTypes[], float initialValue,
                            int treeSize, int numTrees, int maxCSplitSize);
        """)
        lib = _getAbsPath("PRmm/analysis/gbm/tree_predict.so")
        self._C = ffi.dlopen(lib)
        self._ffi = ffi

    def featuresRequired(self):
        return list(self._varNames)

    def predict(self, featuresDict):
        # features is dict[str -> feature]
        # returns [prediction]
        new  = self._ffi.new
        cast = self._ffi.cast

        def cIntA(arr):   return cast("int*",   arr.ctypes.data)
        def cFloatA(arr): return cast("float*", arr.ctypes.data)
        def cInt(x):      return cast("int",    x)
        def cFloat(x):    return cast("float",  x)

        nVars = len(self._varNames)
        nObs  = len(featuresDict[self._varNames[0]])

        cFeatures = new("float*[]", nVars)
        for i, varName in enumerate(self._varNames):
            cFeatures[i] = cFloatA(featuresDict[varName])

        output = np.empty(nObs, dtype=np.float32)

        self._C.innerPredict(cFloatA(output),
                             cFeatures,
                             cInt(nObs),
                             cIntA(self._leftNodes),
                             cIntA(self._rightNodes),
                             cIntA(self._missingNodes),
                             cFloatA(self._splitCodes),
                             cIntA(self._splitVar),
                             cIntA(self._cSplits),
                             cIntA(self._varTypes),
                             cFloat(self._initialValue),
                             cInt(self._treeSize),
                             cInt(self._nTrees),
                             cInt(self._maxCSplits))

        return output




m = GbmModel(_getAbsPath("PRmm/analysis/gbm/resources/2-3-0_P6-C4_insert.tree.h5"), "InsertionModel/Phase1", 10)
fd = { v : np.zeros(100, dtype=np.float32) for v in m.featuresRequired() }
y = m.predict(fd)
