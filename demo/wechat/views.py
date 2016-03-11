# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from datetime import datetime
import hashlib
import json
import xmltodict
from logging import getLogger
from django.core.cache import caches
from django.conf import settings
from django.http import HttpResponse
from wechatpy.replies import TextReply
from wechatpy.utils import to_text
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from wechat.utils import get_component
from wechat.models import Wechat
from wechat import consts
from wechat import caches as wechat_caches
from wechat.tasks import process_wechat_query_auth_code_test


common_logger = getLogger('django.request.common')


class WechatDetailView(APIView):
    model = Wechat
    queryset = Wechat.objects.all()
    lookup_field = 'alias'

    def get_serializer_class(self):
        """
        匿名用户显示简化的信息
        """
        if self.request.user.is_anonymous():
            return wechat_serializers.WechatLiteSerializer
        else:
            return self.serializer_class

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class AuthEventProcessView(APIView):
    """
    处理授权事件
    """
    permission_classes = ()

    def post(self, request, *args, **kwargs):
        """
        处理微信服务器提交的数据
        """
        logger = getLogger('django.request.AuthEventProcessView')
        message = self.preprocess_message(request)
        logger.info('收到事件:{0}'.format(message))
        component = get_component()
        # 推送component_verify_ticket协议
        if message['InfoType'].lower() == 'component_verify_ticket':
            component.cache_component_verify_ticket(
                request.body,
                request.query_params['msg_signature'],
                request.query_params['timestamp'],
                request.query_params['nonce']
            )
            logger.info('成功获取component_verify_ticket')
            return HttpResponse('success')
        # 取消授权通知
        elif message['InfoType'].lower() == 'unauthorized':
            authorizer_appid = message['AuthorizerAppid']
            try:
                wechat = Wechat.objects.get(appid=authorizer_appid)
            except Wechat.DoesNotExist:
                return HttpResponse('success')
            wechat.authorized = False
            wechat.save()
            return HttpResponse('success')
        else:
            pass

    def preprocess_message(self, request):
        '''
        将消息转换成字典
        '''
        component = get_component()
        content = component.crypto.decrypt_message(
            request.body,
            request.query_params['msg_signature'],
            int(request.query_params['timestamp']),
            int(request.query_params['nonce'])
        )
        message = xmltodict.parse(to_text(content))['xml']
        cc = json.loads(json.dumps(message))
        cc['CreateTime'] = int(cc['CreateTime'])
        cc['CreateTime'] = datetime.fromtimestamp(cc['CreateTime'])
        if 'MsgId' in cc:
            cc['MsgId'] = int(cc['MsgId'])
        return cc


class ProcessServerEventView(APIView):
    """
    公众号消息与事件接收
    """
    permission_classes = ()

    def post(self, request, *args, **kwargs):
        logger = getLogger('django.request.ProcessServerEventView')
        appid = kwargs.get('appid', '')
        wechat = Wechat.objects.get(appid=appid)
        message = self.preprocess_message(request)
        # 发布应用时，被开放平台调用
        if appid == settings.TEST_APPID:
            return self.test(request, message, wechat)
        # 发布以后
        else:
            if message.get('MsgType').lower() == 'event':
                return self.process_event(message, wechat)
            elif message.get('MsgType').lower() in consts.MESSAGE_TYPES:
                # 保存消息到数据库
                message_obj = self.save_message(message, wechat)
                # 默认的消息回应
                reply_content = '欢迎！请您稍等，马上给您安排服务人员。'
                return self.reply_message(message_obj, reply_content)
            else:
                return HttpResponse('')

    def test(self, request, message, wechat):
        """
        发布中测试
        """
        logger = getLogger('django.request.test_ProcessServerEventView')
        logger.info(message)
        if message.get('MsgType').lower() == 'event':
            reply = TextReply()
            reply.target = message['FromUserName']
            reply.source = message['ToUserName']
            reply.content = message['Event'] + 'from_callback'
            xml_str = reply.render()
            headers = {'CONTENT_TYPE': request.META['CONTENT_TYPE']}
            return Response(xml_str, headers=headers)
        elif message.get('MsgType').lower() in consts.MESSAGE_TYPES:
            if message.get('Content') == 'TESTCOMPONENT_MSG_TYPE_TEXT':
                reply = TextReply()
                reply.target = message['FromUserName']
                reply.source = message['ToUserName']
                reply.content = 'TESTCOMPONENT_MSG_TYPE_TEXT_callback'
                xml_str = reply.render()
                headers = {'CONTENT_TYPE': request.META['CONTENT_TYPE']}
                return Response(xml_str, headers=headers)
            elif message.get('Content').startswith('QUERY_AUTH_CODE'):
                from datetime import timedelta
                now = datetime.utcnow() + timedelta(seconds=2)
                query_auth_code = message.get('Content').split(':')[1]
                process_wechat_query_auth_code_test.apply_async(
                    (message['FromUserName'], query_auth_code), eta=now)
                return Response('')


    def reply_message(self, message, content):
        """
        回复公众号消息
        """
        reply = TextReply()
        reply.target = message.FromUserName
        reply.source = message.ToUserName
        reply.content = content
        xml_str = reply.render()
        headers = {'CONTENT_TYPE': self.request.META['CONTENT_TYPE']}
        return Response(xml_str, headers=headers)

    def preprocess_message(self, request):
        component = get_component()
        content = component.crypto.decrypt_message(
            request.body,
            request.query_params['msg_signature'],
            int(request.query_params['timestamp']),
            int(request.query_params['nonce'])
        )
        message = xmltodict.parse(to_text(content))['xml']
        cc = json.loads(json.dumps(message))
        cc['CreateTime'] = int(cc['CreateTime'])
        cc['CreateTime'] = datetime.fromtimestamp(cc['CreateTime'])
        if 'MsgId' in cc:
            cc['MsgId'] = int(cc['MsgId'])
        return cc


class WechatAuthPageView(APIView):
    """
    生成授权页面链接
    """

    def get(self, request, *args, **kwargs):
        logger = getLogger('django.request.WechatAuthPageView')
        component = get_component()
        result = component.create_preauthcode()
        auth_url = settings.AUTH_URL.format(
            component_appid=settings.COMPONENT_APP_ID,
            pre_auth_code=result['pre_auth_code'],
            redirect_uri=settings.AUTH_REDIRECT_URI
        )
        return Response({'auth_url': auth_url})


class WechatAuthSuccessPageView(APIView):
    """
    授权成功时回调视图
    """

    def post(self, request, *args, **kwargs):
        logger = getLogger('django.request.WechatAuthSuccessPageView')
        auth_code = request.data['auth_code']
        component = get_component()
        # 拿到授权公众号的信息
        result = component.query_auth(auth_code)
        authorizer_appid = result['authorization_info']['authorizer_appid']
        expires_in = result['authorization_info']['expires_in']
        access_token_key = wechat_caches.CACHE_WECHAT_ACCESS_CODE.format(authorizer_appid)
        refresh_token_key = wechat_caches.CACHE_WECHAT_REFRESH_CODE.format(authorizer_appid)
        app_info = component.get_authorizer_info(authorizer_appid)
        if not Wechat.objects.filter(appid=authorizer_appid).exists():
            wechat = Wechat.objects.create_from_api_result(app_info)
            # wechat.owner = request.user
            # wechat.save()
        else:
            wechat = Wechat.objects.get(appid=authorizer_appid)
            if not wechat.authorized:
                wechat.authorized = True
                wechat.save()
        caches['wechat'].set(
            access_token_key,
            result['authorization_info']['authorizer_access_token'],
            expires_in
        )
        caches['wechat'].set(
            refresh_token_key,
            result['authorization_info']['authorizer_refresh_token'],
            expires_in
        )
        return HttpResponse('success')
