from docopt import docopt
import sys, os.path as op
from glob import glob

from pbcore.io import readFofn
from pbcore.util.Process import backticks

from PRmm.model._utils import *
from PRmm.model import Fixture

__doc__ = \
"""
Usage:
  mkFixture [-n <sectionName>] (-s <secondaryJobPath> | -j <secondaryJobId>)
  mkFixture -m <milhousePath>
"""

def fromSmrtPortalPath(jobPath):
    # reckon the reports path from the input fofn ...
    reportsPaths = set([ updir(path) for path in readFofn(op.join(jobPath, "input.fofn"))])
    if len(reportsPaths) > 1:
        raise ValueError, "No support for multi-movie jobs yet"
    else:
        reportsPath = list(reportsPaths)[0]
        basFname = findOneOrNone("*.bas.h5", reportsPath) or findOneOrNone("*.bax.h5", reportsPath)
        plsFname = findOneOrNone("*.pls.h5", reportsPath) or findOneOrNone("*.plx.h5", reportsPath)
        trcFname = findOneOrNone("*.trc.h5", updir(reportsPath))
        alnFname = findOneOrNone("*.cmp.h5", op.join(jobPath, "data"))
        return Fixture(trcFname=trcFname, plsFname=plsFname,
                       basFname=basFname, alnFname=alnFname)

def fromSmrtLinkPath(jobPath):
    raise NotImplementedError

def jobPathType(jobPath):
    # "SMRTPORTAL", "SMRTLINK", or "UNKNOWN"
    if not op.isdir(jobPath):
        raise ValueError, "Job path must be a reachable directory"
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
    if args["-m"]:
        print "Milhouse support not yet implemented"
        sys.exit(1)
    if args["-s"]:
        fx = fromSecondaryJobPath(args["<secondaryJobPath>"])
    elif args["-j"]:
        fx = fromSecondaryJobId(args["<secondaryJobId>"])
    print fx.toIni(args["<sectionName>"] if args["-n"] else None)



if __name__ == '__main__':
    main()
