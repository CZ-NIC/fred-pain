#!/usr/bin/python3
"""Setup script for fred_pain."""
import os
from distutils.command.build import build

from setuptools import find_packages, setup
from setuptools.command.sdist import sdist

import fred_pain


class custom_build(build):
    sub_commands = [('compile_catalog', lambda x: True)] + build.sub_commands


class custom_sdist(sdist):

    def run(self):
        self.run_command('compile_catalog')
        # sdist is an old style class so super cannot be used
        sdist.run(self)

    def has_i18n_files(self):
        return bool(self.distribution.i18n_files)


def readme():
    """Return content of README file."""
    with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as f:
        return f.read()


SETUP_REQUIRES = ['Babel >=2.3']
INSTALL_REQUIRES = open('requirements.txt').read().splitlines()
EXTRAS_REQUIRE = {'quality': ['isort', 'flake8', 'pydocstyle', 'mypy', 'polint'],
                  'test': ['Django>=1.11', 'django-money']}

setup(name='fred-pain',
      version=fred_pain.__version__,
      description='PAIN interface for FRED',
      long_description=readme(),
      url='https://fred.nic.cz',
      author='Jan Musílek',
      author_email='jan.musilek@nic.cz',
      packages=find_packages(),
      include_package_data=True,
      setup_requires=SETUP_REQUIRES,
      install_requires=INSTALL_REQUIRES,
      extras_require=EXTRAS_REQUIRE,
      python_requires='>=3.5',
      cmdclass={'build': custom_build, 'sdist': custom_sdist},
      classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Plugins',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
      ],
      dependency_links=open('dependency_links.txt').read().splitlines())
