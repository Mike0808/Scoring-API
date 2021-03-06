import hashlib
import json
import store

redis_client = store.RedisClient()


def get_score(phone, email, birthday=None, gender=None, first_name=None, last_name=None):
    key_parts = [
        first_name or "",
        last_name or "",
        str(phone) or "",
        str(birthday) if birthday is not None else "",
    ]
    key = "uid:" + hashlib.md5("".join(key_parts).encode('utf-8')).hexdigest()
    # try get from cache,
    # fallback to heavy calculation in case of cache miss
    score = store.cache_get(redis_client.conn, key) or 0
    if score:
        return score
    if phone:
        score += 1.5
    if email:
        score += 1.5
    if birthday and gender:
        score += 1.5
    if first_name and last_name:
        score += 0.5
    # cache for 60 minutes
    store.cache_set(redis_client.conn, key, score, 60 * 60)
    return score


def get_interests(cid):
    r = store.get(redis_client.conn, "i:%s" % cid)
    return json.loads(r) if r else []
