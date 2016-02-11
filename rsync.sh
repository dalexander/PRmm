#!/bin/bash
rsync --exclude='.git/'  --exclude build --exclude dist --exclude PRmm.egg-info \
 -avx  $(pwd) login14-biofx01:/home/UNIXHOME/dalexander/Projects/rsync/
