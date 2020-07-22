pyembedpg
=========

[![pypi](http://img.shields.io/pypi/v/pyembedpg.png)](https://pypi.python.org/pypi/pyembedpg)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/Pyembedpg.svg)](https://pypi.python.org/pypi/pyembedpg/)
[![pypi downloads](http://img.shields.io/pypi/dm/pyembedpg.png)](https://pypi.python.org/pypi/pyembedpg)
[![Build Status](https://travis-ci.org/Simulmedia/pyembedpg.svg)](https://travis-ci.org/Simulmedia/pyembedpg)
[![License](https://img.shields.io/pypi/l/Pyembedpg.svg)](https://pypi.python.org/pypi/pyembedpg/)
[![Codacy Badge](https://www.codacy.com/project/badge/391726fcad274a24b1427abf5fa10380)](https://www.codacy.com/app/francois-dangngoc/pyembedpg)
[![Coverage Status](https://coveralls.io/repos/Simulmedia/pyembedpg/badge.svg?branch=master&service=github)](https://coveralls.io/github/Simulmedia/pyembedpg?branch=master)

Provide a platform neutral way to run Postgres in integration tests. More info at: http://www.simulmedia.com/resources/blog/pyembedpg-simple-way-use-postgres-python-integration-tests/

### Why

- Running tests in parallel on different instances of Postgres
- Testing on different versions can be useful (e.g., prod has another version of Postgres installed)
- Easier to install a particular version than manually
- Dropping databases and users all the time is painful (and cleanup might not be done properly everytime)

### Features

It downloads the specified version of Postgres automatically from https://ftp.postgresql.org/pub/source/,
build it and cache it in `.pyembedpg` so subsequent uses won't download it.
You can start the Postgres server on any port in a context (using `with`) that will be shutdown when you exit the context.


### How to use it

You can install pyembedpg with pip:

	pip install pyembedpg

You can start a new postgres server as follows:
```python
    pg = PyEmbedPg('9.4.0')
    # Start the database and download it and build it if it hasn't been done so already
    with pg.start(15432) as db:
        # do your thing
```
or:
```python
    pg = PyEmbedPg('9.4.0')
    # Start the database and download it and build it if it hasn't been done so already
    db = pg.start(15432)
    try:
        # do your thing
    finally:
        db.shutdown()
```

If you don't specify the version (e.g., `PyEmbedPg()`), it will use the latest version found in `.pyembedpg` or on the FTP server if `.pyembedpg` is empty.

If you want to use the current Postgres version installed on the server you can do `PyEmbedPg('local')`.

You can use it as follows:
```python
pg = PyEmbedPg('9.4.0')
with pg.start(15432) as postgres:
    postgres.create_user('scott', 'tiger')
    postgres.create_database('testdb', 'scott')

    # Postgres is initialized, now run some queries
    with psycopg2.connect(database='postgres', user='scott', password='tiger', port=postgres.running_port) as conn:
        with conn.cursor() as cursor:
            cursor.execute('CREATE TABLE employee(name VARCHAR(32), age INT)')
            cursor.execute("INSERT INTO employee VALUES ('John', 32)")
            cursor.execute("INSERT INTO employee VALUES ('Mary', 22)")
            cursor.execute('SELECT * FROM employee ORDER BY age')
            assert cursor.fetchall() == [('Mary', 22), ('John', 32)]
```

or in unit tests:
```python
import unittest
import psycopg2
from pyembedpg import PyEmbedPg


class TestPyEmbedPgWithContext(unittest.TestCase):
    def setUp(self):
        self.postgres = PyEmbedPg('9.4.0').start(15432)

    def test_simple_run(self):
        self.postgres.create_user('scott', 'tiger')
        self.postgres.create_database('testdb', 'scott')

        # Postgres is initialized, now run some queries
        with psycopg2.connect(database='postgres', user='scott', password='tiger', port=self.postgres.running_port) as conn:
            with conn.cursor() as cursor:
                cursor.execute('CREATE TABLE employee(name VARCHAR(32), age INT)')
                cursor.execute("INSERT INTO employee VALUES ('John', 32)")
                cursor.execute("INSERT INTO employee VALUES ('Mary', 22)")
                cursor.execute('SELECT * FROM employee ORDER BY age')
                assert cursor.fetchall() == [('Mary', 22), ('John', 32)]

    def tearDown(self):
        self.postgres.shutdown()
```

You can also specify a list of ports to use (e.g., `PyEmbedPg('9.4.0').start(range(15432, 15440))`). The first available port will be used. This can be useful when you run multiple tests in parallel.

### Troubleshooting

#### Error while building postgres

Check that gcc and readline (e.g., libreadline-dev on Debian, readline on MacOS) are installed.

### Alternatives
Alternatively, there is another project [testing.postgres](https://github.com/tk0miya/testing.postgresql) that allows to use the current Postgres application
installed on the server and initialize a new instance.

### Contributors

* Lukmanul Hakim [@kimkimkeren](https://github.com/kimkimkeren)
