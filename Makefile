
install: clean
	python setup.py install

clean:
	-rm -rf dist/ build/ *.egg-info
	-rm -rf doc/_build
	-rm -f nosetests.xml
	-find . -name "*.pyc" | xargs rm -f

test:
	nosetests tests

REMOTE_HOST := login14-biofx01
REMOTE_PATH := /home/UNIXHOME/dalexander/Projects/rsync/PRmm
REMOTE      := ${REMOTE_HOST}:${REMOTE_PATH}

rpush:
	rsync --exclude='.git/'  --exclude build --exclude dist --exclude PRmm.egg-info \
	      -avx  $(shell pwd) $(shell dirname ${REMOTE})

rpull:
	rsync --exclude='.git/'  --exclude build --exclude dist --exclude PRmm.egg-info \
	      -avx  ${REMOTE} $(shell dirname $(shell pwd))

notebook:
	jupyter notebook notebooks/

rnotebook-server:
	# Remotely, launch a new screen session "nbserver"; in that screen, launch the notebook
	ssh ${REMOTE_HOST} "cd ${REMOTE_PATH} && workon VE && screen -S nbserve -d -m jupyter notebook --no-browser --ip=0.0.0.0 ."

rnotebook-tunnel:
	ssh -L 18888:${REMOTE_HOST}:8888 ${REMOTE_HOST}

rnotebook-browse:
	open "http://localhost:18888"


.PHONY: install clean rpull rpush notebook rnotebook-browse rnotebook-tunnel rnotebook-server tests
