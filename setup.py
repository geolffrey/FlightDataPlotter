#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Skeleton is an example Python package.
# Copyright (c) 2009-2012 Flight Data Services Ltd
# http://www.flightdataservices.com

try:
    from setuptools import setup, find_packages
except ImportError:
    from distribute_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

from skeleton import __version__ as VERSION
from requirements import RequirementsParser
requirements = RequirementsParser()

setup(
    name='Skeleton',
    version=VERSION,   
    author='Flight Data Services Ltd',
    author_email='developers@flightdataservices.com',
    description='A Skeleton Python Package',    
    long_description=open('README').read() + open('CHANGES').read(),
    license='Other/Proprietary License',
    url='http://www.flightdatacommunity.com/',
    download_url='',    
    packages=find_packages(exclude=['distribute_setup', 'requirements', \
    'tests']),
    # The 'include_package_data' keyword tells setuptools to install any 
    # data files it finds specified in the MANIFEST.in file.    
    include_package_data=True,
    zip_safe=False,
    install_requires=requirements.install_requires,
    setup_requires=requirements.setup_requires,
    tests_require=requirements.tests_require,
    extras_require=requirements.extras_require,
    dependency_links=requirements.dependency_links,
    test_suite='nose.collector',
    platforms=[
        'OS Independent',
    ],        
    keywords=['example', 'skeleton', 'python', 'package'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: Other/Proprietary License',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Operating System :: OS Independent',
        'Topic :: Software Development',
    ],
    scripts=['skeleton/scripts/skull.py', 'skeleton/scripts/cross_bones.py'],
    entry_points = """
        [console_scripts]
        cross_bones_too = skeleton.scripts.cross_bones:run
        skull_too = skeleton.scripts.skull:run
        
        #[gui_scripts]
        #skull_gui = skeleton.gui.skull_gui:run
        """,                   
)
