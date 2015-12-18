
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
