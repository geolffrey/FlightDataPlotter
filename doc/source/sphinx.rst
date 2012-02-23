{{{
sphinx-quickstart
}}}}}}}}}}}}}}}}}
Welcome to the Sphinx 1.1.2 quickstart utility.

Please enter values for the following settings (just press Enter to
accept a default value, if one is given in brackets).

Enter the root path for documentation.
> Root path for the documentation [.]: doc

You have two options for placing the build directory for Sphinx output.
Either, you use a directory "_build" within the root path, or you separate
"source" and "build" directories within the root path.
> Separate source and build directories (y/N) [n]: y

Inside the root directory, two more directories will be created; "_templates"
for custom HTML templates and "_static" for custom stylesheets and other static
files. You can enter another prefix (such as ".") to replace the underscore.
> Name prefix for templates and static dir [_]:

The project name will occur in several places in the built documentation.
> Project name: Skeleton
> Author name(s): Flight Data Services Ltd

Sphinx has the notion of a "version" and a "release" for the
software. Each version can have multiple releases. For example, for
Python the version is something like 2.5 or 3.0, while the release is
something like 2.5.1 or 3.0a1.  If you don't need this dual structure,
just set both to the same value.
> Project version: 0.1.0
> Project release [0.1.0]:

The file name suffix for source files. Commonly, this is either ".txt"
or ".rst".  Only files with this suffix are considered documents.
> Source file suffix [.rst]:

One document is special in that it is considered the top node of the
"contents tree", that is, it is the root of the hierarchical structure
of the documents. Normally, this is "index", but if your "index"
document is a custom template, you can also set this to another filename.
> Name of your master document (without suffix) [index]:

Sphinx can also add configuration for epub output:
> Do you want to use the epub builder (y/N) [n]:

Please indicate if you want to use one of the following Sphinx extensions:
> autodoc: automatically insert docstrings from modules (y/N) [n]: y
> doctest: automatically test code snippets in doctest blocks (y/N) [n]: y
> intersphinx: link between Sphinx documentation of different projects (y/N) [n]: y
> todo: write "todo" entries that can be shown or hidden on build (y/N) [n]: y
> coverage: checks for documentation coverage (y/N) [n]: y
> pngmath: include math, rendered as PNG images (y/N) [n]: y
> mathjax: include math, rendered in the browser by MathJax (y/N) [n]: n
> ifconfig: conditional inclusion of content based on config values (y/N) [n]: n
> viewcode: include links to the source code of documented Python objects (y/N) [n]: y

A Makefile and a Windows command file can be generated for you so that you
only have to run e.g. `make html' instead of invoking sphinx-build
directly.
> Create Makefile? (Y/n) [y]:
> Create Windows command file? (Y/n) [y]:

Creating file doc/source/conf.py.
Creating file doc/source/index.rst.
Creating file doc/Makefile.
Creating file doc/make.bat.

Finished: An initial directory structure has been created.

You should now populate your master file doc/source/index.rst and create other documentation
source files. Use the Makefile to build the docs, like so:
   make builder
where "builder" is one of the supported builders, e.g. html, latex or linkcheck

Change this in doc/source/conf.py.

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath('../skeleton'))
