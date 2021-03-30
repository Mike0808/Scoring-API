import time
import random
import json
import redis
import os

REDIS_AUTH = {
    'PASSWORD': os.environ.get('REDIS_PASSWORD'),
    'HOST': '127.0.0.1',
    'PORT': 6379,
    'HEALTH': 10
}


def conn_exist(db, timeoffset=3):
    pool = redis.ConnectionPool(
        host=REDIS_AUTH['HOST'],
        port=REDIS_AUTH['PORT'],
        db=db,
        password=REDIS_AUTH['PASSWORD'],
        health_check_interval=REDIS_AUTH['HEALTH'],
        socket_timeout=REDIS_AUTH['HEALTH'] * 3,
    )
    for i in range(3):
        try:
            r = redis.StrictRedis(connection_pool=pool)
            conn = pool.get_connection('_')
            if conn:
                return r
            time.sleep(timeoffset)
        except redis.exceptions.ConnectionError:
            continue
    return False


def cache_set(key, score, period, db=0):
    i = 0
    r = conn_exist(db)
    if r:
        rsetter = r.set(name=key, value=score, ex=period)
    return rsetter


def cache_get(db=0, key=None):
    r = conn_exist(db)
    if r:
        try:
            rgetter = float(r.get(key).decode('UTF-8'))
            return rgetter
        except AttributeError:
            return False


def get(key, db=1):
    r = conn_exist(db)
    if r:
        l = r.get('list:interests').decode('UTF-8').split(',')
        res = '["' + '","'.join(random.sample(l, 2)) + '"]'
        return res
    else:
        return False
