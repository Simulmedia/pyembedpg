#!/usr/bin/env python

import sys
from setuptools import setup
from setuptools.command.test import test as TestCommand

class PyTestCommand(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)

setup(
    name='pyembedpg',
    version='0.0.1',
    description='Run embedded version of Postgres',
    long_description='Run embedded version of Postgres',
    keywords='postgres, python, tests',
    license='Apache License 2.0',
    author='Simulmedia',
    author_email='francois@simulmedia.com',
    url='http://github.com/simulmedia/pyembedpg/',
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    install_requires=[
        'requests==2.7.0',
        'psycopg2==2.6'
    ],
    tests_require=[
        'pytest'
    ],
    test_suite='tests',
    cmdclass={
        'test': PyTestCommand
    }
)
