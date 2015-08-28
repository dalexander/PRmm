
install: clean
	python setup.py install

clean:
	-rm -rf dist/ build/ *.egg-info
	-rm -rf doc/_build
	-rm -f nosetests.xml
	-find . -name "*.pyc" | xargs rm -f
