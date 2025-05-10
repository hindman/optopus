#! /usr/bin/env python

from os.path import dirname, realpath, join
from setuptools import setup, find_packages
import sys

####
# Basic project info.
####

project_name = 'argle'
package_name = project_name.replace('-', '_')
repo_name    = project_name
description  = 'Command line arguments done right'
url          = 'https://github.com/hindman/' + repo_name
author       = 'Monty Hindman'
author_email = 'mhindman@gmail.com'
license      = 'MIT'
src_subdir   = 'src'
project_dir  = dirname(realpath(__file__))

####
# Requirements.
####

reqs = (
    'kwexception',
    'short-con',
)

extras = {
    'test' : (
        'pytest-cov',
        'tox',
    ),
    'dev' : (
        'build',
        'invoke',
        'ipython',
        'pycodestyle',
        'twine',
        'virtualenv',
        'virtualenvwrapper',
    ),
}

####
# Set __version__, long description, and classifiers.
####

version_file = join(project_dir, src_subdir, package_name, 'version.py')
exec(open(version_file).read())

readme_file = join(project_dir, 'README.md')
long_desc = open(readme_file).read()
long_desc_type = 'text/markdown'

classifiers = [
    'Development Status :: 3 - Alpha',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'Topic :: Software Development',
]

####
# Packages and scripts.
####

packages = find_packages(where = src_subdir)

package_data = {
    package_name: [],
}

####
# Install.
####

setup(
    name = project_name,
    version = __version__,
    author = author,
    author_email = author_email,
    url = url,
    description = description,
    zip_safe = False,
    packages = packages,
    package_dir = {'': src_subdir},
    package_data = package_data,
    install_requires = reqs,
    tests_require = extras['test'],
    extras_require = extras,
    license = license,
    long_description = long_desc,
    long_description_content_type = long_desc_type,
    classifiers = classifiers,
)

