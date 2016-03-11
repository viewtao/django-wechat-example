#-*- coding:utf-8 -*-
from __future__ import unicode_literals
from wechatpy import WeChatComponent
from django.conf import settings
from django.core.cache import caches


def get_component():
    """
    获取开放平台API对象
    """
    component = WeChatComponent(
        settings.COMPONENT_APP_ID,
        settings.COMPONENT_APP_SECRET,
        settings.COMPONENT_APP_TOKEN,
        settings.COMPONENT_ENCODINGAESKEY,
        session=caches['wechat']
    )
    return component
