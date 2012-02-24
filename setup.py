#!/usr/bin/env python

import re

try:
    from setuptools import setup, find_packages
except ImportError:
    from distribute_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

def parse_requirements(file_name):
    """
    Extract all dependency names from requirements.txt.
    """
    requirements = []
    for line in open(file_name, 'r').read().split('\n'):
        if re.match(r'(\s*#)|(\s*$)', line):
            continue
        if re.match(r'\s*-e\s+', line):
            # TODO support version numbers
            requirements.append(re.sub(r'\s*-e\s+.*#egg=(.*)$', r'\1', line))
        elif re.match(r'\s*-f\s+', line):
            pass
        else:
            requirements.append(line)

    requirements.reverse()
    return requirements

def parse_dependency_links(file_name):
    """
    Extract all URLs for packages not found on PyPI.
    """
    dependency_links = []
    for line in open(file_name, 'r').read().split('\n'):
        if re.match(r'\s*-[ef]\s+', line):
            dependency_links.append(re.sub(r'\s*-[ef]\s+', '', line))

    dependency_links.reverse()
    return dependency_links

from skeleton import __version__ as VERSION

# Reference
#  - http://packages.python.org/distribute/setuptools.html

setup(
    name='Skeleton',
    version = VERSION,
    url='http://www.flightdataservices.com/',
    author='Flight Data Services Ltd',
    author_email='developers@flightdataservices.com',            
    description='A Skeleton Python Package',    
    long_description=open('README').read(),    
    download_url='',
    platforms='',
    license='',

    # === Include and Exclude ===
   
    # For simple projects, it's usually easy enough to manually add packages to 
    # the packages argument of setup(). However, for very large projects it can 
    # be a big burden to keep the package list updated. That's what 
    # setuptools.find_packages() is for.

    # find_packages() takes a source directory, and a list of package names or 
    # patterns to exclude. If omitted, the source directory defaults to the 
    # same directory as the setup script. Some projects use a src or lib 
    # directory as the root of their source tree, and those projects would of 
    # course use "src" or "lib" as the first argument to find_packages(). 
    # (And such projects also need something like package_dir = {'':'src'} in 
    # their setup() arguments, but that's just a normal distutils thing.)

    # Anyway, find_packages() walks the target directory, and finds Python 
    # packages by looking for __init__.py files. It then filters the list of 
    # packages using the exclusion patterns.

    # Exclusion patterns are package names, optionally including wildcards. For 
    # example, find_packages(exclude=["*.tests"]) will exclude all packages 
    # whose last name part is tests. Or, find_packages(exclude=["*.tests", 
    # "*.tests.*"]) will also exclude any subpackages of packages named tests, 
    # but it still won't exclude a top-level tests package or the children 
    # thereof. The exclusion patterns are intended to cover simpler use cases 
    # than this, like excluding a single, specified package and its subpackages.

    # Regardless of the target directory or exclusions, the find_packages() 
    # function returns a list of package names suitable for use as the packages 
    # argument to setup(), and so is usually the easiest way to set that 
    # argument in your setup script. Especially since it frees you from having 
    # to remember to modify your setup script whenever your project grows 
    # additional top-level packages or subpackages.

    packages = find_packages(exclude=['tests']),
                
    # You can specify data files to be included in your packages. Use 
    # the include_package_data keyword. This tells setuptools to install any 
    # data files it finds specified in the distutils' MANIFEST.in file.
    include_package_data = True, 
    # If you want finer-grained control over what files are included (for 
    # example, if you have documentation files in your package directories and 
    # want to exclude them from installation), then you can also use the 
    # package_data keyword.
    # - http://docs.python.org/distutils/setupscript.html#installing-package-data
            
    # Parse the 'requirements.txt' file to determine the dependencies.
    install_requires = parse_requirements('requirements.txt'), 
    dependency_links = parse_dependency_links('requirements.txt'),
    setup_requires = ['nose'],
    tests_require = ['mock'],
    extras_require = {
        'jenkins': ['clonedigger', 'nosexcover', 'pep8', 'pyflakes', 'pylint'],
        'sphinx': ['sphinx', 'sphinx-pypi-upload'],
        'test': ['mock'],        
    },
    test_suite = 'nose.collector',

    # === Script Creation ===
        
    # Scripts are files containing Python source code, intended to be started 
    # from the command line. Scripts don't require Distutils to do anything very 
    # complicated. The only clever feature is that if the first line of the 
    # script starts with #! and contains the word "python", the Distutils will 
    # adjust the first line to refer to the current interpreter location. By 
    # default, it is replaced with the current interpreter location. 

    # The scripts option simply is a list of files to be handled in this way. 
    scripts=['skeleton/scripts/skull.py', 'skeleton/scripts/cross_bones.py'],

    # === Entry Points ===
    
    # Packaging and installing scripts can be a bit awkward using the method 
    # above For one thing, there's no easy way to have a script's filename match 
    # local conventions on both Windows and POSIX platforms. For another, you 
    # often have to create a separate file just for the "main" script, when your 
    # actual "main" is a function in a module somewhere. 

    # setuptools fixes all of these problems by automatically generating scripts 
    # for you with the correct extension, and on Windows it will even create an 
    # .exe file so that users don't have to change their PATHEXT settings. The 
    # way to use this feature is to define "entry points" in your setup script 
    # that indicate what function the generated script should import and run. 
    # It is possible to create console scripts and GUI scripts.        
        
    # Two notations are popular, I'll only document the most readable.
    
    entry_points = """
        [console_scripts]
        cross_bones_too = skeleton.scripts.cross_bones:run
        skull_too = skeleton.scripts.skull:run
        
        #[gui_scripts]
        #skull_gui = skeleton.gui.skull_gui:run
        """,               
    zip_safe = False,
    
    # I've included a selection of classifiers that are typical for FDS, simply
    # delete the inappropriate entries or add new classifiers using the 
    # following URL for reference.
    #  - http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers = [
        "Development Status :: 3 - Alpha",
    	"Development Status :: 4 - Beta",
        "Development Status :: 5 - Production/Stable",  	
        "Environment :: Console",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Operating System :: OS Independent",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    	],        
    )
