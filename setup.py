"""
Usage:
    python setup.py test
    python setup.py install
    python setup.py py2app
"""

import os
from setuptools import setup, find_packages

from Motome.config import VERSION


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

APP = ['./Motome.py']
DATA_FILES = []
PY2APP_PLIST = {'CFBundleShortVersionString': VERSION}
PY2APP_OPTIONS = {'argv_emulation': True,
               'resources':'./Motome/styles',
               'iconfile':'./deployment/Icons/logo.icns',
               'plist': PY2APP_PLIST}

setup(
    name='Motome',
    version=VERSION,
    author='Aaron Kehrer',
    author_email='akehrer@in2being.com',
    description=('Motome is a note taking and information aggregation application '
                 'inspired by many other note taking programs.'),
    keywords = "note-taking qt pyside  markdown",
    packages=find_packages(),
    include_package_data=True,
    long_description=read('DESCRIPTION.rst'),
    install_requires = ['Markdown', 'PySide', 'PyYAML'],
    license='BSD',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': PY2APP_OPTIONS},
    setup_requires=['py2app'],
    entry_points = {
        'gui_scripts': ['Motome = Motome:main']
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: X11 Applications",
        "Environment :: MacOS X",
        "Environment :: Win32 (MS Windows)",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
    test_suite='tests',
)
