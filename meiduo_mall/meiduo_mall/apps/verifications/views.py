from django.shortcuts import render
from django.views import View
from django.http import HttpResponse
from django_redis import get_redis_connection
from meiduo_mall.libs.captcha.captcha import captcha

# Create your views here.
class ImagecodeView(View):
    '''定义验证码类'''
    def get(self,request,uuid):

        text,image=captcha.generate_captcha()
        redis_conn = get_redis_connection('verify_code')
        redis_conn.setex('img_%s'%uuid,300,text)
        return HttpResponse(image,content_type='image/jpg')
