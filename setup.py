from setuptools import setup, find_packages, Extension

globals = {}
execfile("PRmm/__init__.py", globals)
__VERSION__ = globals["__VERSION__"]

setup(
    name = "PRmm",
    version=__VERSION__,
    author="Pacific Biosciences",
    author_email="dalexander@pacificbiosciences.com",
    packages = find_packages(),
    include_package_data=True,
    package_data={"PRmm.analysis.gbm" : ["resources/*.h5"]},
    zip_safe = False,
    install_requires=[
        "pbcore >= 0.9.3",
        "numpy >= 1.6.0",
        "h5py >= 2.0.1",
        ]
    )

