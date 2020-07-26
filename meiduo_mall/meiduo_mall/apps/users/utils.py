from django.contrib.auth.backends import ModelBackend
import re
from .models import User


def get_user_account(account):
    '''判断account是否是手机号,并返回user'''
    try:
        if re.match('^1[3-9]\d{9}$',account):
            # 根据手机号获得用户名
            user = User.objects.get(mobile=account)
        else:
            # 根据用户名获得用户名
            user = User.objects.get(username=account)
    except Exception:
        return None
    else:
        return user


class UsernameMobileAuthBackend(ModelBackend):
    '''自定义用户认证后端'''

    def authenticate(self, request, username=None, password=None, **kwargs):

        user = get_user_account(username)

        if user and user.check_password(password):
            return user
