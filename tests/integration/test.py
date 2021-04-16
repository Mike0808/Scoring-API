import re
import time
import unittest
from time import sleep

import redis

import store

redis_client = store.RedisClient()

class TestSuite(unittest.TestCase):
    def setUp(self):
        self.key = 'test_cache'
        self.score = 3.0
        self.conn = redis_client

    def set_cache_set(self, timeout=3):
        return store.cache_set(self.conn.conn, key=self.key, score=self.score, period=timeout)

    def get_cache_get(self):
        return store.cache_get(self.conn.conn, key=self.key)

    def test_conn_exist(self):
        '''
        Проверка подключения к Redis
        '''
        # r = store.conn_exist(db=0)
        self.assertEqual(type(self.conn.conn), redis.Redis)

    def test_cache_setter(self):
        '''
        Проверка записи в Redis значения {self.key = 'test_cache'
        self.score = 3.0}
        :return: True
        '''
        sset = self.set_cache_set()
        self.assertEqual(sset, True)

    def test_cache_getter(self):
        '''
        Проверка считывания из Redis
        :return: self.score
        '''
        self.set_cache_set()
        self.assertEqual(self.get_cache_get(), self.score)

    def test_non_cache_getter(self):
        '''
        Проверка периода (3 сек) хранения записи в Redis для
        проверки реализации процедуры хранения данных в течении 1 часа
        :return: False
        '''
        sleep(3)
        self.assertEqual(self.get_cache_get(), None)

    def test_get(self):
        '''
        Проверка функции формирования интересов пользователя
        :return: list(интересы)
        '''
        pattern = r'^\[[,"\w].*\]$'
        getter = store.get(self.conn.conn, 'list:interests')
        leng = len(getter)
        match = re.match(pattern, getter)
        self.assertEqual(match.endpos, leng)

    def test_not_conn_exist(self):
        '''
        Проверка недоступености Redis
        :return:
        '''
        try:
            g = self.conn.pool.get_connection('_')
            r = self.conn.conn
            if g:
                r.shutdown(nosave=True)
            self.conn.pool.get_connection('_')
        except redis.exceptions.ConnectionError as e:
            return True

    def test_reconnect_to_redis(self):
        '''
        Test reconnecting to redis after fall
        :return:
        '''
        g = self.conn.conn
        self.assertEqual(g, None)


if __name__ == "__main__":
    unittest.main()
