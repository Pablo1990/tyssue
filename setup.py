import os
import sys
import subprocess

from setuptools import setup
from setuptools import find_packages


DISTNAME = 'tyssue'
DESCRIPTION = 'tyssue is a living tissues, cell level, modeling library'
LONG_DESCRIPTION = ('tyssue uses the scientific python ecosystem and CGAL'
                    ' LinearCellComplex library to model epithelium at the'
                    ' cellular level')
MAINTAINER = 'Guillaume Gay'
MAINTAINER_EMAIL = 'guillaume@damcb.com'
URL = 'https://github.com/DamCB/tyssue'
LICENSE = 'MPL'
DOWNLOAD_URL = 'https://github.com/DamCB/tyssue.git'

files = ['*.so*', '*.a*', '*.lib*',
         'config/*/*.json', 'stores/*.*']

## Version management copied form numpy
## Thanks to them!
MAJOR               = 0
MINOR               = 1
MICRO               = 0
ISRELEASED          = True
VERSION             = '%d.%d.%d' % (MAJOR, MINOR, MICRO)


def git_version():
    def _minimal_ext_cmd(cmd):
        # construct minimal environment
        env = {}
        for k in ['SYSTEMROOT', 'PATH']:
            v = os.environ.get(k)
            if v is not None:
                env[k] = v
        # LANGUAGE is used on win32
        env['LANGUAGE'] = 'C'
        env['LANG'] = 'C'
        env['LC_ALL'] = 'C'
        out = subprocess.Popen(cmd, stdout = subprocess.PIPE, env=env).communicate()[0]
        return out

    try:
        out = _minimal_ext_cmd(['git', 'rev-parse', 'HEAD'])
        GIT_REVISION = out.strip().decode('ascii')
    except OSError:
        GIT_REVISION = "Unknown"

    return GIT_REVISION


def get_version_info():
    # Adding the git rev number needs to be done inside write_version_py(),
    # otherwise the import of tyssue.version messes up the build under Python 3.
    FULLVERSION = VERSION
    if os.path.exists('.git'):
        GIT_REVISION = git_version()
    elif os.path.exists('tyssue/version.py'):
        # must be a source distribution, use existing version file
        try:
            from numpy.version import git_revision as GIT_REVISION
        except ImportError:
            raise ImportError("Unable to import git_revision. Try removing " \
                              "numpy/version.py and the build directory " \
                              "before building.")
    else:
        GIT_REVISION = "Unknown"

    if not ISRELEASED:
        FULLVERSION += '.dev0+' + GIT_REVISION[:7]

    return FULLVERSION, GIT_REVISION


def write_version_py(filename='tyssue/version.py'):
    cnt = """
# THIS FILE IS GENERATED FROM tyssue SETUP.PY
#
short_version = '%(version)s'
version = '%(version)s'
full_version = '%(full_version)s'
git_revision = '%(git_revision)s'
release = %(isrelease)s
if not release:
    version = full_version
"""
    FULLVERSION, GIT_REVISION = get_version_info()

    a = open(filename, 'w')
    try:
        a.write(cnt % {'version': VERSION,
                       'full_version' : FULLVERSION,
                       'git_revision' : GIT_REVISION,
                       'isrelease': str(ISRELEASED)})
    finally:
        a.close()

if __name__ == "__main__":

    write_version_py()
    setup(
        name=DISTNAME,
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        maintainer=MAINTAINER,
        maintainer_email=MAINTAINER_EMAIL,
        url=URL,
        license=LICENSE,
        download_url=DOWNLOAD_URL,
        version=VERSION,
        classifiers=["Development Status :: 4 - Beta",
                     "Intended Audience :: Science/Research",
                     "License :: OSI Approved :: MPL v2.0",
                     "Natural Language :: English",
                     "Operating System :: MacOS",
                     "Operating System :: Microsoft",
                     "Operating System :: POSIX :: Linux",
                     "Programming Language :: Python :: 3.4",
#                     "Programming Language :: Python :: Implementation :: CPython",
                     "Topic :: Scientific/Engineering :: Bio-Informatics",
                     "Topic :: Scientific/Engineering :: Medical Science Apps",
                     ],

        packages=find_packages(),
        package_data={'tyssue': files},
        include_package_data=True,
        zip_safe=False
    )
