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

import unittest
import psycopg2
from pyembedpg import PyEmbedPg


class TestPyEmbedPg(unittest.TestCase):
    def setUp(self):
        self.port = 15433
        self.embedpg = PyEmbedPg('9.4.0')
        self.postgres = self.embedpg.start(self.port)
        self.postgres.create_user('scott', 'tiger')
        self.postgres.create_database('testdb', 'scott')

    def test_simple_run(self):
        # Postgres is initialized, now run some queries
        with psycopg2.connect(database='postgres', user='scott', password='tiger', host='localhost', port=self.port) as conn:
            with conn.cursor() as cursor:
                cursor.execute('CREATE TABLE employee(name VARCHAR(32), age INT)')
                cursor.execute("INSERT INTO employee VALUES ('John', 32)")
                cursor.execute("INSERT INTO employee VALUES ('Mary', 22)")
                cursor.execute('SELECT * FROM employee ORDER BY age')
                assert cursor.fetchall() == [('Mary', 22), ('John', 32)]

        # Test that the version is installed locally
        assert self.embedpg.get_latest_local_version() is not None

    def tearDown(self):
        self.postgres.shutdown()
