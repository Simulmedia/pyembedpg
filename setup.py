#!/usr/bin/env python

#
# Copyright 2015 Simulmedia, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

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
    version='0.0.5',
    description='Run embedded version of Postgres',
    long_description='Run embedded version of Postgres',
    keywords='postgres, python, tests',
    license='Apache License 2.0',
    author='Simulmedia',
    author_email='francois@simulmedia.com',
    url='http://github.com/simulmedia/pyembedpg/',
    packages=[''],
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    install_requires=[
        'requests',
        'psycopg2'
    ],
    tests_require=[
        'pytest'
    ],
    test_suite='tests',
    cmdclass={
        'test': PyTestCommand
    }
)
