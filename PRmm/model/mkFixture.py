from docopt import docopt
import os.path as op
from glob import glob

from pbcore.io import readFofn
from pbcore.


from ._utils import *

__doc__ = \
"""
Usage:
  mkFixture [-n <sectionName>] (-s <secondaryPath> | -j <secondaryJobId>)
  mkFixture -m <milhousePath>
"""


def fromPaths(reportsPath, secondaryJobPath=None):
    basFname = findOneOrNone("*.bas.h5", reportsPath)
    plsFname = findOneOrNone("*.pls.h5", reportsPath)
    trcFname = findOneOrNone("*.trc.h5", updir(reportsPath))
    if secondaryJobPath:
        alnFname = findOneOrNone("*.cmp.h5", op.join(secondaryJobPath, "data"))
    else:
        alnFname = None
    return ReadersFixture(trcFname=trcFname, plsFname=plsFname,
                          basFname=basFname, alnFname=alnFname)

def fromSmrtPortalPath(jobPath):
    # reckon the reports path from the input fofn ...
    reportsPaths = set([ updir(path) for path in readFofn(op.join(jobPath, "input.fofn"))])
    if len(reportsPaths) > 1:
        raise ValueError, "No support for multi-movie jobs yet"
    else:
        reportsPath = list(reportsPaths)[0]
        return ReadersFixture.fromPaths(reportsPath, jobPath)


def fromSmrtLinkPath(jobPath):
    raise NotImplementedError

def jobPathType(jobPath):
    # "SMRTPORTAL", "SMRTLINK", or "UNKNOWN"
    if findOneOrNone("input.fofn", jobPath):
        return "SMRTPORTAL"
    elif findOneOrNone("workflow/entry-points.json", jobPath):
        return "SMRTLINK"
    else:
        return "UNKNOWN"

def fromSecondaryJobPath(jobPath):
    type = jobPathType(jobPath)
    if type == "SMRTPORTAL":
        return fromSmrtPortalPath(jobPath)
    elif type == "SMRTLINK":
        return fromSmrtLinkPath(jobPath)
    else:
        raise ValueError, "Unrecognized secondary job type"

def resolveSecondaryJobId(jobId):
    return backticks("ssh login14-biofx01 pbls %s" % str(jobId))[0][0]

def fromSecondaryJobId(jobId):
    return fromSecondaryJobPath(resolveSecondaryJobId(jobId))

def main():
    args = docopt(__doc__)
    fx = Fixture.fromIniFile(args["<iniFile>"], args["<sectionName>"])
    print fx

if __name__ == '__main__':
    main()



# Make a tool for building fixtures conveniently,

# mkFixture [--name sectionName] path1 [path2] >> file.ini
#  (dwim from the two paths.  sectionName defaults to something)


    # @staticmethod
    # def fromSecondaryJobPath(jobPath):
    #     # reckon the reports path from the input fofn ...
    #     reportsPaths = set([ updir(path) for path in readFofn(op.join(jobPath, "input.fofn"))])
    #     if len(reportsPaths) > 1:
    #         raise ValueError, "No support for multi-movie jobs yet"
    #     else:
    #         reportsPath = list(reportsPaths)[0]
    #         return ReadersFixture.fromPaths(reportsPath, jobPath)

    # @staticmethod
    # def fromPaths(reportsPath, secondaryJobPath=None):
    #     basFname = findOneOrNone("*.bas.h5", reportsPath)
    #     plsFname = findOneOrNone("*.pls.h5", reportsPath)
    #     trcFname = findOneOrNone("*.trc.h5", updir(reportsPath))
    #     if secondaryJobPath:
    #         alnFname = findOneOrNone("*.cmp.h5", op.join(secondaryJobPath, "data"))
    #     else:
    #         alnFname = None
    #     return ReadersFixture(trcFname=trcFname, plsFname=plsFname,
    #                           basFname=basFname, alnFname=alnFname)

    # @staticmethod
    # def fromTraceSplitPaths(reportsPath, secondaryJobPath=None):
    #     # ARGGH!
    #     trcFnames = find("*split*.trc.h5", op.join(updir(reportsPath), "traceSplit"))
    #     trcFofn = tempfile.NamedTemporaryFile(suffix=".trc.fofn", delete=False)
    #     for fname in trcFnames:
    #         trcFofn.file.write(fname)
    #         trcFofn.file.write("\n")
    #     trcFofn.close()
    #     basFname = findOneOrNone("*.bas.h5", reportsPath)
    #     plsFname = findOneOrNone("*.pls.h5", reportsPath)
    #     if secondaryJobPath:
    #         alnFname = findOneOrNone("*.cmp.h5", op.join(secondaryJobPath, "data"))
    #     else:
    #         alnFname = None
    #     return ReadersFixture(trcFname=trcFofn.name, plsFname=plsFname,
    #                           basFname=basFname, alnFname=alnFname)
