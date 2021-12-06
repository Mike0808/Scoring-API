import time
import random
import json
import redis
import os

REDIS_AUTH = {
    'PASSWORD': os.environ.get('REDIS_PASSWORD'),
    'HOST': '127.0.0.1',
    'PORT': 6379,
    'HEALTH': 10,
    'DB': 0
}


class RedisClient:
    def __init__(self,
                 host=REDIS_AUTH['HOST'],
                 port=REDIS_AUTH['PORT'],
                 db=REDIS_AUTH['DB'],
                 password=REDIS_AUTH['PASSWORD'],
                 health_check_interval=REDIS_AUTH['HEALTH'],
                 socket_timeout=REDIS_AUTH['HEALTH'] * 3):
        self._host = host
        self._port = port
        self._db = db
        self._password = password
        self._health = health_check_interval
        self._timeout = socket_timeout
        self.pool = redis.ConnectionPool(
            host=self._host,
            port=self._port,
            db=self._db,
            password=self._password,
            health_check_interval=self._health,
            socket_timeout=self._timeout,
        )

    @property
    def conn(self):
        for reconnect in range(4):
            try:
                if not hasattr(self, '_conn'):
                    self.get_connection()
                else:
                    if self.pool.get_connection("_"):
                        return self._conn
                    time.sleep(self._health)
                    self.get_connection()
                    if reconnect == 3:
                        return
            except redis.exceptions.ConnectionError:
                continue

    def get_connection(self):
        self._conn = redis.StrictRedis(connection_pool=self.pool)


class PersistConnection:

    def __init__(self, redis_client, score=None, period=None,  key=None):
        self.redis_client = redis_client
        self.conn = self.redis_client.conn
        self.key = key
        self.score = score
        self.period = period

    def conn_exist(self, redis_client):
        return redis_client.conn

    def cache_set(self):
        if self.conn:
            rsetter = self.conn.set(name=self.key, value=self.score, ex=self.period)
            return rsetter
        return None

    def cache_get(self):
        if self.conn:
            if self.conn.exists(self.key):
                rgetter = float(self.conn.get(self.key).decode('UTF-8'))
                return rgetter

    def get(self):
        if self.conn:
            l = self.conn.get('list:interests').decode('UTF-8').split(',')
            res = '["' + '","'.join(random.sample(l, 2)) + '"]'
            return res
        return False
