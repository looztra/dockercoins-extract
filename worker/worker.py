import logging
import os
from redis import Redis
import requests
import time

DEBUG = os.environ.get("DEBUG", "").lower().startswith("y")

log = logging.getLogger(__name__)
if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("requests").setLevel(logging.WARNING)

redis_host = os.environ.get("DOCKERCOINS_REDIS_HOST")
redis_port = os.environ.get("DOCKERCOINS_REDIS_PORT")
rng_host = os.environ.get("DOCKERCOINS_RNG_HOST")
rng_port = os.environ.get("DOCKERCOINS_RNG_PORT")
hasher_host = os.environ.get("DOCKERCOINS_HASHER_HOST")
hasher_port = os.environ.get("DOCKERCOINS_HASHER_PORT")

if redis_host is None:
    log.info("using default value for redis_host")
    redis_host = 'redis'
else:
    log.info("found value '{}' for redis_host in env".format(redis_host))

if redis_port is None:
    log.info("using default value for redis_port")
    redis_port = 6379
else:
    log.info("found value '{}' for redis_port in env".format(redis_port))

if rng_host is None:
    log.info("using default value for rng_host")
    rng_host = 'rng'
else:
    log.info("found value '{}' for rng_host in env".format(rng_host))

if rng_port is None:
    log.info("using default value for rng_port")
    rng_port = 80
else:
    log.info("found value '{}' for rng_port in env".format(rng_port))

if hasher_host is None:
    log.info("using default value for hasher_host")
    hasher_host = 'hasher'
else:
    log.info("found value '{}' for hasher_host in env".format(hasher_host))

if hasher_port is None:
    log.info("using default value for hasher_port")
    hasher_port = 80
else:
    log.info("found value '{}' for hasher_port in env".format(hasher_port))


redis = Redis(host=redis_host, port=redis_port)


def get_random_bytes():
    r = requests.get("http://" + rng_host + ":" + str(rng_port) + "/32")
    return r.content


def hash_bytes(data):
    r = requests.post("http://" + hasher_host + ":" + str(hasher_port) + "/",
                      data=data,
                      headers={"Content-Type": "application/octet-stream"})
    hex_hash = r.text
    return hex_hash


def work_loop(interval=1):
    deadline = 0
    loops_done = 0
    while True:
        if time.time() > deadline:
            log.info("{} units of work done, updating hash counter"
                     .format(loops_done))
            redis.incrby("hashes", loops_done)
            loops_done = 0
            deadline = time.time() + interval
        work_once()
        loops_done += 1


def work_once():
    log.debug("Doing one unit of work")
    time.sleep(0.1)
    random_bytes = get_random_bytes()
    hex_hash = hash_bytes(random_bytes)
    if not hex_hash.startswith('0'):
        log.debug("No coin found")
        return
    log.info("Coin found: {}...".format(hex_hash[:8]))
    created = redis.hset("wallet", hex_hash, random_bytes)
    if not created:
        log.info("We already had that coin")


if __name__ == "__main__":
    while True:
        try:
            work_loop()
        except:
            log.exception("In work loop:")
            log.error("Waiting 10s and restarting.")
            time.sleep(10)
