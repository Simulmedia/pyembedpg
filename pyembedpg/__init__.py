from distutils import spawn
import logging
import os
from os.path import expanduser
import re
import tempfile
from psycopg2._psycopg import OperationalError
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import requests
import tarfile
import shutil
import psycopg2
import time
from natsort import natsorted
from subprocess import Popen


logger = logging.getLogger('pyembedpg')


class PyEmbedPg(object):

    DOWNLOAD_BASE_URL = 'http://ftp.postgresql.org/pub/source'
    DOWNLOAD_URL = DOWNLOAD_BASE_URL + '/v{version}/postgresql-{version}.tar.bz2'
    LOCAL_VERSION = 'local'

    CACHE_DIRECTORY = '.pyembedpg'

    def __init__(self, version=None):
        """
        Initialize a new Postgres object
        :param version: version to use. If it is not set, use the latest version in .pyembedpg directory. If not present
                        use the latest version remotely. Use 'local' to use the local postgres version installed on the machine
        :return:
        """
        home_dir = expanduser("~")
        self._cache_dir = os.path.join(home_dir, PyEmbedPg.CACHE_DIRECTORY)

        # if version is not specified, check local last version otherwise get last remote version
        self.version = version
        if not self.version:
            self.version = self.get_latest_local_version()
            if not self.version:
                self.version = self.get_latest_remote_version()

        if version == PyEmbedPg.LOCAL_VERSION:
            full_path = spawn.find_executable('postgres')
            if not full_path:
                raise PyEmbedPgException('Cannot find postgres executable. Make sure it is in your path')
            self._version_path = os.path.dirname(full_path)
        else:
            self._version_path = os.path.join(self._cache_dir, self.version)

    def get_latest_local_version(self):
        """
        Return the latest version installed in the cache
        :return: latest version installed locally in the cache and None if there is nothing downloaded
        """

        return natsorted(os.listdir(self._cache_dir))[0] if os.path.exists(self._cache_dir) else None

    def get_latest_remote_version(self):
        """
        Return the latest version on the Postgres FTP server
        :return: latest version installed locally on the Postgres FTP server
        """
        response = requests.get(PyEmbedPg.DOWNLOAD_BASE_URL)
        last_version_match = list(re.finditer('>v(?P<version>[^<]+)<', response.content))[-1]
        return last_version_match.group('version')

    def check_version_present(self):
        """
        Check if the version is present in the cache
        :return: True if the version has already been downloaded and build, False otherwise
        """
        return os.path.exists(self._version_path)

    def download_and_unpack(self):
        # if the version we want to download already exists, do not do anything
        if self.check_version_present():
            logger.debug('Version {version} already present in cache'.format(version=self.version))
            return

        url = PyEmbedPg.DOWNLOAD_URL.format(version=self.version)
        response = requests.get(url, stream=True)

        if not response.ok:
            raise PyEmbedPgException('Cannot download file {url}. Error: {error}'.format(url=url, error=response.content))

        with tempfile.NamedTemporaryFile() as fd:
            logger.debug('Downloading {url}'.format(url=url))
            for block in response.iter_content(chunk_size=4096):
                fd.write(block)
            fd.flush()
            # Unpack the file into temporary dir
            temp_dir = tempfile.mkdtemp()
            source_dir = os.path.join(temp_dir, 'postgresql-{version}'.format(version=self.version))
            try:
                with tarfile.open(fd.name) as tar:
                    tar.extractall(temp_dir)
                os.system('sh -c "cd {path} && ./configure --prefix={target_dir} && make install"'.format(path=source_dir, target_dir=self._version_path))
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)

    def start(self, port=5432):
        """
        Start a new Postgres server on the specified port
        :param port: port to connect to, can be an int or a list of ports
        :return:
        """
        if not self.check_version_present():
            self.download_and_unpack()

        bin_dir = os.path.join(self._version_path, 'bin')
        ports = [port] if isinstance(port, int) else port
        return DatabaseRunner(bin_dir, ports)


class DatabaseRunner(object):
    ADMIN_USER = 'root'
    TIMEOUT = 10

    def __init__(self, bin_dir, ports):
        self._ports = ports
        self._postgres_cmd = os.path.join(bin_dir, 'postgres')

        # init db
        init_db = os.path.join(bin_dir, 'initdb')
        self._temp_dir = tempfile.mkdtemp()
        command = init_db + ' -D ' + self._temp_dir + ' -U ' + DatabaseRunner.ADMIN_USER
        logger.debug('Running command: {command}'.format(command=command))
        os.system(command)

        # overwrite pg_hba.conf to only allow local access with password authentication
        with open(os.path.join(self._temp_dir, 'pg_hba.conf'), 'w') as fd:
            fd.write(
                '# TYPE  DATABASE        USER            ADDRESS                 METHOD\n'
                '# "local" is for Unix domain socket connections only\n'
                'local   all             {admin}                                 trust\n'
                'local   all             all                                     md5\n'
                'host    all             {admin}         127.0.0.1/32            trust\n'
                'host    all             all             127.0.0.1/32            md5\n'
                '# IPv6 local connections:\n'
                'host    all             {admin}         ::1/128                 trust\n'
                'host    all             all             ::1/128                 md5\n'.format(admin=DatabaseRunner.ADMIN_USER)
            )

        for port in ports:
            self.proc = Popen([self._postgres_cmd, '-D', self._temp_dir, '-p', str(port)])
            # if the process is still running, then there was problem, most likely the port is taken so try the next one
            if not self.proc.poll():
                self.running_port = port
                break
        else:
            raise PyEmbedPgException('Cannot run postgres on any of these ports [{ports}]'.format(ports=', '.join((str(p) for p in ports))))

        # Loop until the server is started
        logger.debug('Waiting for Postgres to start...')
        start = time.time()
        while time.time() - start < DatabaseRunner.TIMEOUT:
            try:
                with psycopg2.connect(database='postgres', user=DatabaseRunner.ADMIN_USER, host='localhost', port=self.running_port):
                    break
            except OperationalError:
                pass
            time.sleep(0.1)
        else:
            raise PyEmbedPgException('Cannot start postgres after {timeout} seconds'.format(timeout=DatabaseRunner.TIMEOUT))

        logger.debug('Postgres started on port {port}...'.format(port=self.running_port))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

    def create_user(self, username, password):
        """Create a user
        :param username:
        :type username: basestring
        :param password:
        :type password: basestring
        """
        with psycopg2.connect(database='postgres', user=DatabaseRunner.ADMIN_USER, host='localhost', port=self.running_port) as conn:
            with conn.cursor() as cursor:
                cursor.execute("CREATE USER {username} WITH ENCRYPTED PASSWORD '{password}'".format(username=username, password=password))

    def create_database(self, name, owner=None):
        """Create a new database
        :param name: database name
        :type name: basestring
        :param owner: username of the owner or None if unspecified
        :type owner: basestring
        """
        with psycopg2.connect(database='postgres', user=DatabaseRunner.ADMIN_USER, host='localhost', port=self.running_port) as conn:
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            with conn.cursor() as cursor:
                sql = 'CREATE DATABASE {name} ' + ('WITH OWNER {owner}' if owner else '')
                cursor.execute(sql.format(name=name, owner=owner))

    def shutdown(self):
        """
        Shutdown postgres and remove the data directory
        """
        # stop pg
        try:
            logger.info('Killing postgres on port {port}'.format(port=self.running_port))
            self.proc.kill()
            os.waitpid(self.proc.pid, 0)
        finally:
            logger.info('Removing postgres data dir on {dir}'.format(dir=self._temp_dir))
            # remove data directory
            shutil.rmtree(self._temp_dir, ignore_errors=True)


class PyEmbedPgException(Exception):
    pass