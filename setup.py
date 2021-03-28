#! /usr/bin/env python

from os.path import dirname, realpath, join
from setuptools import setup, find_packages
import sys


####
# Basic metadata.
####

project_name = 'optopus'
package_name = project_name.replace('-', '_')
repo_name    = project_name
src_subdir   = 'src'
description  = 'Option parsing done right'
url          = 'https://github.com/hindman/' + repo_name
author       = 'Monty Hindman'
author_email = 'mhindman@gmail.com'


####
# Requirements.
####

reqs = [
    'six>=1.10.0',
]

extras = {
    'test' : [
        'coverage>=4.1',
        'pytest-cache>=1.0',
        'pytest-cov>=2.3.0',
        'pytest>=2.9.2',
        'tox>=2.3.1',
    ],
    'dev' : [
        'Pygments>=2.1.3',
        'Sphinx >=1.4.4, <1.5',
        'pep8>=1.7.0',
        'invoke',
        'pycodestyle',
        'twine',
        'short-con',
    ],
}


####
# Packages and scripts.
####

packages = find_packages(where = src_subdir)

package_data = {
    package_name: [
        'REVISION',
    ],
}

####
# Import __version__.
####

project_dir = dirname(realpath(__file__))
version_file = join(project_dir, src_subdir, package_name, 'version.py')
exec(open(version_file).read())


####
# Install.
####

setup(
    name             = project_name,
    version          = __version__,
    author           = author,
    author_email     = author_email,
    url              = url,
    description      = description,
    zip_safe         = False,
    packages         = packages,
    package_dir      = {'': src_subdir},
    package_data     = package_data,
    install_requires = reqs,
    tests_require    = extras['test'],
    extras_require   = extras,
)

