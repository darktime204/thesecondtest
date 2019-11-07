# 1.导包
import re

from django.conf import settings
from django.contrib.auth.backends import ModelBackend

# 2. 类继承
from apps.users.models import User


# 生成 激活 链接
def generate_verify_email_url(user):
    # 1. user_id email
    dict_data = {'user_id': user.id, 'email': user.email}

    # 2.参数加密
    from utils.secret import SecretOauth
    secret_data = SecretOauth().dumps(dict_data)

    # 3.拼接 完整的路由
    verify_url = settings.EMAIL_ACTIVE_URL + '?token=' + secret_data

    return verify_url


# 封装函数
def get_user_by_account(account):
    try:
        if re.match('^1[3456789]\d{9}$', account):
            user = User.objects.get(mobile=account)
            # 2. username
        else:
            user = User.objects.get(username=account)

    except User.DoesNotExist:
        return None
    else:
        return user


class UsernameMobileAuthBackend(ModelBackend):
    # 3. 重写authenticate函数
    def authenticate(self, request, username=None, password=None, **kwargs):
        # 1.校验用户名
        user = get_user_by_account(username)
        # 2.校验 密码
        if user and user.check_password(password):
            return user
