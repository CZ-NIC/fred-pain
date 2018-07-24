#!/usr/bin/python3
"""Setup script for fred_pain."""
import os

from setuptools import find_packages, setup

import fred_pain


def readme():
    """Return content of README file."""
    with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as f:
        return f.read()


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
      install_requires=INSTALL_REQUIRES,
      extras_require=EXTRAS_REQUIRE,
      python_requires='>=3.5',
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
