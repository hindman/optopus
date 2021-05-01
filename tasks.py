#! /usr/bin/env python

####
#
# General:
#   inv [--dry] TASK [OPTIONS]
#   inv --list
#   inv --help TASK
#
# Tasks:
#   inv tags
#   inv test [--cov]
#   inv dist [--publish] [--test]
#   inv tox
#   inv bump [--kind <major|minor|patch>] [--local]
#
####

from invoke import task

@task
def tags(c):
    '''
    Run mtags for the project
    '''
    c.run('mtags --recipe .optpy --write w')
    c.run('mtags --recipe .opttxt --write u --toc order')

@task
def test(c, cov = False):
    '''
    Run pytest, optional opening coverage report.
    '''
    cov_args = '--cov optopus --cov-report html' if cov else ''
    cmd = 'pytest -s -v {} tests'.format(cov_args)
    c.run(cmd)
    if cov:
        c.run('open htmlcov/index.html')

@task
def tox(c):
    '''
    Run tox for the project
    '''
    d = dict(PYENV_VERSION = '3.9.4:3.8.9:3.7.10:3.6.13:3.5.10')
    c.run('tox', env = d)

@task
def dist(c, publish = False, test = False):
    '''
    Create distribution, optionally publishing to pypi or testpypi.
    '''
    repo = 'testpypi' if test else 'pypi'
    c.run('rm -rf dist')
    c.run('python setup.py sdist bdist_wheel')
    c.run('echo')
    c.run('twine check dist/*')
    if publish:
        c.run(f'twine upload -r {repo} dist/*')

@task
def bump(c, kind = 'minor', local = False):
    '''
    Version bump (minor, major, patch). Commits, pushes unless --local.
    '''
    # Validate.
    bump_types = dict(major = 0, minor = 1, patch = 2)
    assert kind in bump_types
    # Get current version as a 3-element list.
    path = 'src/optopus/version.py'
    lines = open(path).readlines()
    version = lines[0].split("'")[1]
    major, minor, patch = [int(x) for x in version.split('.')]
    # Compute new version.
    tup = (
        (major + 1, 0, 0) if kind == 'major' else
        (major, minor + 1, 0) if kind == 'minor' else
        (minor, minor, patch + 1)
    )
    version = '.'.join(str(x) for x in tup)
    # Write new version file.
    if c['run']['dry']:
        print('# Dry: modify version.py.')
    else:
        with open(path, 'w') as fh:
            fh.write(f"__version__ = '{version}'\n\n")
        print(f'Bumped to {version}.')
    # Commit and push.
    if not local:
        c.run(f"git commit {path} -m 'Version {version}'")
        c.run('git push origin master')

