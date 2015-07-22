import unittest
import psycopg2
from pyembedpg import PyEmbedPg


class TestPyEmbedPg(unittest.TestCase):
    def setUp(self):
        self.port = 15433
        self.postgres = PyEmbedPg('9.4.0').start(self.port)
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

    def tearDown(self):
        self.postgres.shutdown()
