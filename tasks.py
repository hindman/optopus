#! /usr/bin/env python

####
#
# General:
#   invoke [--dry] TASK [OPTIONS]
#   invoke --list
#   invoke --help TASK
#
# Tasks:
#   invoke test [--cov]
#   invoke publish
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

# @task
# def test(c, cov = False):
#     '''
#     Run pytest, optional opening coverage report.
#     '''
#     cov_args = '--cov short_con --cov-report html' if cov else ''
#     cmd = 'pytest -s -v {} tests'.format(cov_args)
#     c.run(cmd)
#     if cov:
#         c.run('open htmlcov/index.html')

# @task
# def dist(c, publish = False, repo = 'pypi'):
#     '''
#     Create software distribution, optionally publishing it to pypi.
#     '''
#     c.run('rm -rf dist')
#     c.run('python setup.py sdist bdist_wheel')
#     c.run('echo')
#     c.run('twine check dist/*')
#     if publish:
#         c.run(f'twine upload -r {repo} dist/*')

# @task
# def bump(c, t = 'minor', local = False):
#     '''
#     Version bump (minor, major, or patch). Commits and pushes unless --local.
#     '''
#     # Validate.
#     bump_types = dict(major = 0, minor = 1, patch = 2)
#     assert t in bump_types
#     # Get current version as a 3-element list.
#     path = 'src/short_con/version.py'
#     lines = open(path).readlines()
#     version = lines[0].split("'")[1]
#     major, minor, patch = [int(x) for x in version.split('.')]
#     # Compute new version.
#     tup = (
#         (major + 1, 0, 0) if t == 'major' else
#         (major, minor + 1, 0) if t == 'minor' else
#         (minor, minor, patch + 1)
#     )
#     version = '.'.join(str(x) for x in tup)
#     # Write new version file.
#     with open(path, 'w') as fh:
#         fh.write(f"__version__ = '{version}'\n\n")
#     print(f'Bumped to {version}.')
#     # Commit and push.
#     if not local:
#         c.run(f"git commit {path} -m 'Version {version}'")
#         c.run('git push origin master')

