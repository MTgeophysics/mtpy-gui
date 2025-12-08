#!/usr/bin/env python

import sys
# Test Python's version
major, minor = sys.version_info[0:2]
if ((major, minor) < (3, 5)) or (major, minor) > (3, 13):
    sys.stderr.write('\nPython 3.5 to 3.8 is needed to use this package\n')
    sys.exit(1)


from setuptools import find_packages, setup
from distutils.command.sdist import sdist
cmdclass={'sdist': sdist}

# def readme():
#     with open('README.rst', encoding='utf-8', mode='r') as f:
#         return f.read()


# Get the version from the MtPy-gui module.
with open("mtpy_gui/__init__.py") as f:
    for line in f:
        if line.find("__version__") >= 0:
            version = line.split("=")[1].strip()
            version = version.strip('"')
            version = version.strip("'")

setup(name='MtPy_gui',
    packages=find_packages(),
    scripts=[],
    version=version,
    description='Data handling',
    long_description='', # readme(),
    url = '',
    #classifiers=[
    #    'Development Status :: 3 - Alpha',
    #    'License :: OSI Approved',
    #    'License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication',
    #    'Programming Language :: Python :: 3',
    #    'Topic :: Scientific/Engineering',
    #],
    author='Bennett Hoogenboom',
    author_email='bhooogenboom@usgs.gov',
    install_requires=[
        'mtpy-v2', 
        'pyqt5', 
        'qdarkstyle', 
        'pyvistaqt'
    ],
    #entry_points = {
    #     'console_scripts':[
    #         'MtPy_gui=mtpy_gui:main'
    #     ],
    # }
)

