
## How to install PRmm (headless) on the PacBio cluster environment.

The PacBio cluster machines have a fairly spartan base environment; to
access libraries you need to load "modules".  The following tools and
libraries are required to get a working installation of PRmm.

First, remove any previously loaded modules.

```sh
  $ module purge                                 # Start from a clean environment
```

Load the compiler and native libraries we will link against.
```sh
  $ module load gcc/4.8.2
  $ module load hdf5/1.8.12                      # h5py needs the HDF5 libraries.
  $ module load zlib/1.2.5                       # pysam requires zlib (BAM reading)
```
Now, set up our Python environment
```
  $ module load python/2.7.9                     # Load python
  $ module load virtualenv                       # ... and virtualenv
  $ virtualenv ~/VE-PRmm                         # Build the virtualenv
  $ source VE/bin/activate                       # ... and activate it.
```

Get the PRmm source and install
```sh
  $ git clone https://github.com/dalexander/PRmm # fetch the PRmm source code
  $ cd PRmm
  $ pip install Cython                           # pip is too dumb to figure out this transitive
                                                 # dependency of pbcore, so install it up-front.
  
  $ pip install -r requirements-headless.txt     # Now install the remaining Python dependencies
  
  $ python setup.py develop                      # Finally, install PRmm.
```

If you want to do analysis in an IPython notebook, you want some more stuff.

```sh
  $ module load openblas                         # transitive dependency via scipy

  $ pip install ipython notebook pandas matplotlib seaborn
```
