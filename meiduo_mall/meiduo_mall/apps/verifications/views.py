import logging
import random

logger = logging.getLogger('django')
from django.shortcuts import render
from django.views import View
from django.http import HttpResponse, JsonResponse
from django_redis import get_redis_connection
from meiduo_mall.libs.captcha.captcha import captcha
from meiduo_mall.celery_tasks.sms.tasks import ccp_send_sms_code
from meiduo_mall.libs.yuntongxun.ccp_sms import CCP
# Create your views here.
from users.models import User


class ImagecodeView(View):
    '''定义验证码类'''
    def get(self,request,uuid):

        text,image=captcha.generate_captcha()
        redis_conn = get_redis_connection('verify_code')
        redis_conn.setex('img_%s'%uuid,300,text)
        return HttpResponse(image,content_type='image/jpg')


class SMSCodeView(View):
    '''短信验证码类'''
    def get(self,request,mobile):

        # 将这句话提到前面最开始的位置:
        redis_conn = get_redis_connection('verify_code')
        # 进入函数后, 先获取存储在 redis 中的数据
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        # 查看数据是否存在, 如果存在, 说明60s没过, 返回
        if send_flag:
            return JsonResponse({'code': 400,
                                 'errmsg': '发送短信过于频繁'})

        uuid = request.GET.get('image_code_id')
        image_code_client = request.GET.get('image_code')


        if not all([uuid,image_code_client]):
            return JsonResponse({"code":400,"errmsg":"缺少必传参数"})


        redis_conn = get_redis_connection("verify_code")

        image_code_server = redis_conn.get("img_%s"%uuid)

        if image_code_server is None:
            return JsonResponse({"code":400,"errmsg":"验证码失效"})
        try:
            redis_conn.delete("img_%s"%uuid)
        except Exception as e:
            logger.error(e)

        image_code_server = image_code_server.decode()
        if image_code_client.lower() != image_code_server.lower():
            return JsonResponse({"code":400,"errmsg":"验证码输入错误"})

        sms_code = "%06d"%random.randint(0,999999)
        logger.info(sms_code)

        pl = redis_conn.pipeline()

        pl.setex('send_flag_%s'%mobile,60,1)

        pl.setex('sms_%s'%mobile,300,sms_code)

        pl.excute()

        # CCP().send_template_sms(mobile,[sms_code,5],1)
        ccp_send_sms_code.delay(mobile, sms_code)

        return JsonResponse({"code":0,"errmsg":"短信发送成功"})




