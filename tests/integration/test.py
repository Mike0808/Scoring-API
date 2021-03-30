import unittest
import store
from time import sleep
import redis
import re


class TestSuite(unittest.TestCase):
    def setUp(self):
        self.key = 'test_cache'
        self.score = 3.0

    def set_cache_set(self, timeout=3):
        return store.cache_set(key=self.key, score=self.score, period=timeout)

    def get_cache_get(self):
        return store.cache_get(key=self.key)

    def test_conn_exist(self):
        '''
        Проверка подключения к Redis
        '''
        r = store.conn_exist(db=0)
        self.assertEqual(type(r), redis.Redis)

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
        self.assertEqual(self.get_cache_get(), False)

    def test_get(self):
        '''
        Проверка функции формирования интересов пользователя
        :return: list(интересы)
        '''
        pattern = r'^\[[,"\w].*\]$'
        getter = store.get('list:interests')
        leng = len(getter)
        match = re.match(pattern, getter)
        self.assertEqual(match.endpos, leng)

    def test_not_conn_exist(self):
        '''
        Проверка недоступености Redis
        :return:
        '''
        r = store.conn_exist(db=0)
        if r:
            r.shutdown(nosave=True)
        r = store.conn_exist(db=0)
        self.assertEqual(r, False)

if __name__ == "__main__":
    unittest.main()
