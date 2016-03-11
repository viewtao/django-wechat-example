# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf.urls import url
from wechat import views

urlpatterns = [
    # 处理发给公众号的消息和事件
    url(
       r'^server/(?P<appid>[0-9a-z_]+)/?$',
       views.ProcessServerEventView.as_view(),
       name='wechat-server_messages'
    ),
   # 获取授权链接
   url(
       r'^auth/?$',
       views.WechatAuthPageView.as_view(),
       name='wechat-auth'
   ),
   # 公众号授权成功后由微信服务器调用
   url(
       r'^authorized/?$',
       views.WechatAuthSuccessPageView.as_view(),
       name='wechat-authorized'
   ),
   # 授权事件接收URL
   url(
       r'^callback/?$',
       views.AuthEventProcessView.as_view(),
       name='wechat-component-verify-ticket'
   )
]
