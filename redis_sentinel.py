import redis, os, sys
from loguru import logger

try:
    REDIS_SENTINEL_HOST = os.environ['REDIS_SENTINEL_HOST']
    REDIS_SENTINEL_PORT = os.environ['REDIS_SENTINEL_PORT']
    REDIS_PASSWORD = os.environ['REDIS_PASSWORD']
    REDIS_CLUSTER_NAME = os.environ['REDIS_CLUSTER_NAME']
except KeyError as e:
    logger.error("env not set: {}", e)
    sys.exit(1)

def get_redis_client():
    sentinel_hosts = [(REDIS_SENTINEL_HOST, REDIS_SENTINEL_PORT)]
    service_name = REDIS_CLUSTER_NAME
    sentinel = redis.sentinel.Sentinel(sentinel_hosts, socket_timeout=0.1)
    try:
        master = sentinel.discover_master(service_name)
        logger.info(f'Master is {master}')
        return redis.Redis(host=master[0], port=master[1], password=REDIS_PASSWORD)
    except:
        logger.error(f'No master found for {REDIS_CLUSTER_NAME}')
        sys.exit(1)