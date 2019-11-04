# 1.导包
from django_redis import get_redis_connection


def redis_demo():
    # 2.实例化  链接数据库 redis
    client = get_redis_connection('default')
    # 3.增删改查
    client.set('django_redis_key', 'itheima')