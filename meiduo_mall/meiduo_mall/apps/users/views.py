import json
import re
import logging
logger = logging.getLogger('django')
import random
from django.shortcuts import render
from django.http import JsonResponse
from django.http import HttpResponse
from django.views import View
from django_redis import get_redis_connection
from meiduo_mall.libs.yuntongxun.ccp_sms import CCP
from users.models import User
from django.contrib.auth import login,logout,authenticate
# Create your views here.


class UsernameCountView(View):

    def get(self,request,username):

        try:

            count = User.objects.filter(username=username).count()

        except Exception as e:

            return JsonResponse({"code":404,"errmsg":"访问数据库失败"})

        return JsonResponse({"code":0,"errmsg":"ok","count":count})

class MobileCountView(View):
    '''创建判断用户注册手机号
    是否重复类'''

    def get(self,request,mobile):

        try:
            count = User.objects.filter(mobile=mobile).count()
        except Exception as e:
            return JsonResponse({"code":404,"errmsg":"访问数据库失败"})
        return JsonResponse({"code":200,"errmsg":"ok","count":count})


class SMSCodeView(View):
    """短信验证码"""

    def get(self, reqeust, mobile):

        # 1. 接收参数
        image_code_client = reqeust.GET.get('image_code')
        uuid = reqeust.GET.get('image_code_id')

        # 2. 校验参数
        if not all([image_code_client, uuid]):
            return JsonResponse({'code': 400,
                                 'errmsg': '缺少必传参数'})

        # 3. 创建连接到redis的对象
        redis_conn = get_redis_connection('verify_code')

        # 4. 提取图形验证码
        image_code_server = redis_conn.get('img_%s' % uuid)
        if image_code_server is None:
            # 图形验证码过期或者不存在
            return JsonResponse({'code': 400,
                                 'errmsg': '图形验证码失效'})

        # 5. 删除图形验证码，避免恶意测试图形验证码
        try:
            redis_conn.delete('img_%s' % uuid)
        except Exception as e:
            logger.error(e)

        # 6. 对比图形验证码
        # bytes 转字符串
        image_code_server = image_code_server.decode()
        # 转小写后比较
        if image_code_client.lower() != image_code_server.lower():
            return JsonResponse({'code': 400,
                                 'errmsg': '输入图形验证码有误'})

        # 7. 生成短信验证码：生成6位数验证码
        sms_code = '%06d' % random.randint(0, 999999)
        logger.info(sms_code)

        # 8. 保存短信验证码
        # 短信验证码有效期，单位：300秒
        redis_conn.setex('sms_%s' % mobile, 300, sms_code)

        # 9. 发送短信验证码
        # 短信模板
        CCP().send_template_sms(mobile,[sms_code, 5], 1)

        # 10. 响应结果
        return JsonResponse({'code': 0,
                             'errmsg': '发送短信成功'})


class RegisterView(View):
    '''注册视图'''
    # 接受注册信息
    def post(self,request):

        dict = json.loads(request.body)

        username = dict.get('username')
        password = dict.get('password')
        password2 = dict.get('password2')
        mobile = dict.get('mobile')
        allow = dict.get('allow')
        sms_code_client = dict.get('sms_code')


        if not all([username,password,password2,mobile,allow,sms_code_client]):
            return JsonResponse({"code":400,"errmsg":"缺少必传参数"})


        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$',username):
            return JsonResponse({"code":400,"errmsg":"username格式有误"})


        if not re.match(r'^[a-zA-Z0-9]{8,20}$',password):
            return  JsonResponse({"code":400,"errmsg":"password格式有误"})


        if password != password2:
            return  JsonResponse({"code":400,"errmsg":"两次输入不一致"})


        if not re.match(r'^1[3-9]\d{9}$',mobile):
            return JsonResponse({"code":400,"errmsg":"mobile格式有误"})


        if allow != True:
            return JsonResponse({"code":400,"errmsg":"allow格式有误"})


        redis_conn = get_redis_connection("verify_code")

        sms_code_server = redis_conn.get('sms_%s'%mobile)


        if not sms_code_server:
            return JsonResponse({"code":400,"errmsg":"短信验证码过期"})


        if sms_code_server != sms_code_client:
            return JsonResponse({"code":400,"errmsg":"验证码有误"})

        try:
            user = User.objects.create_user(username=username,password=password,mobile=mobile)
        except Exception:
            return JsonResponse({"code":400,"errmsg":"写入失败"})


        login(request, user)
        response = JsonResponse({'code': 0,'errmsg': 'ok'})

        # 在响应对象中设置用户名信息.
        # 将用户名写入到 cookie，有效期 14 天
        response.set_cookie('username',user.username,max_age=3600 * 24 * 14)
        # 返回响应结果
        return response


class LoginView(View):


    def post(self,request):
        '''实现接口登录'''
        dict = json.loads(request.body)

        username = dict.get("username")
        password = dict.get("password")
        remember = dict.get("remember")


        if not all([username,password]):
            return JsonResponse({"code":400,"errmsg":"缺少必要参数"})

        user = authenticate(username=username,password=password)

        if user is None:
            return JsonResponse({"code":400,"errmsg":"用户名或密码错误"})

        login(request,user)

        if remember != True:
            request.session.set_expiry(0)
        else:
            request.session.set_expiry(None)

        # 生成响应对象
        response = JsonResponse({'code': 0,
                                 'errmsg': 'ok'})

        # 在响应对象中设置用户名信息.
        # 将用户名写入到 cookie，有效期 14 天
        response.set_cookie('username',
                            user.username,
                            max_age=3600 * 24 * 14)

        # 返回响应结果
        return response


class LogoutView(View):
    '''定义退出登录的接口'''
    def delete(self,request):
        '''实现退出登录'''
        logout(request)

        response=JsonResponse({"code":0,"errmsg":"ok"})

        response.delete_cookie('username')

        return response


class UserInfoView(View):
    '''用户中心'''
    def get(self,request):


        return JsonResponse({"code":0,"errmsg":"ok"})

        # if request.user.is_authenticated:
        #
        # else:
        #     class LogoutView(View):




