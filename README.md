PRmm (PulseRecognizer minus minus; pronounced *perm*), is a basic
interactive PacBio trace viewer.  It is portable and simple.

![Screenshot](./screenshot.png)

Additionally, the backend data model of PRmm is designed to be usable
for data analysis from the perspective of a ZMW---providing simple
access to the collated trace, pulsecall, basecall, and alignment data
resulting from the ZMW.

# Using the viewer

   ```
   % prmm --help
   ``` 

# Using the model for data analysis

The basic use concept for the model is:

  1. Load a "Fixture", which consists of a collated set of
     files providing traces (`tr(c|x).h5`), pulses (`bam` or
     `pl(s|x).h5`), bases (`bam` or `bas(s|x).h5`) and alignments
     (`bam` or `cmp.h5`).  For convenience, a fixture can be specified
     in an `ini` file like so:

        ``` 
        [All4Mers-LVP1]
        Comment=All4Mers 1 hour lambda on LVP1 chip
        Traces=/pbi/collections/315/3150005/r54004_20151117_203936/1_A01/m54004_151117_203942.trc.h5
        Analysis=/home/UNIXHOME/dalexander/Projects/git/VariantCallingReports/2015/HQ-Region-Finding/SequelT2B/UnrolledAll4mers
        Bases=%(Analysis)s/m54004_151117_203942.bax.h5
        Pulses=%(Analysis)s/m54004_151117_203942.plx.h5
        Alignment=%(Analysis)s/aligned_reads.cmp.h5
        Reference=%(Analysis)s/All4Mers.fasta
        ```
        
     (note the use of format interpolation here, which is inessential (and nonstandard!)
     but convenient) and then loaded like so:

        ```
        >>> readers = Fixture.fromIniFile("~/.pacbio/data-fixtures.ini", "All4Mers-LVP1")
        ```

  2. "Slice" the ReadersFixture by a holenumber of interest, obtaining
     a "FixtureZmw", which then gives convenient access to the trace
     and analysis data from that ZMW.
        
        ```
        >>> zmw = readers[55]

        >>> zmw.cameraTrace
        array([[  77.40115356,   58.53388214,   58.53388214, ...,   54.8108139 ,
                  51.10409546,   51.10409546],
               [ 104.56507874,   73.59329224,   88.93170166, ...,   66.02966309,
                  58.53388214,   51.10409546], dtype=float32)

        >>> zmw.basecalls
        'AAACATATAACCATGATCAGTAGCTTCTATACAGACAACTAA...'

        >>> z.regions  # Frame-delimited "regions"
         [<Region:     INSERT    1239   73519>,
          <Region:         HQ   22749  134882>,
          <Region:  ALIGNMENT   24020   73356>,
          <Region:    ADAPTER   73543   78439>,
          <Region:     INSERT   78485  134882>,
          <Region:  ALIGNMENT   86953  134882>]
        ```
