# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from logging import getLogger
from django.db import models
from wechat import consts

class WechatManager(models.Manager):
    """
    创建公众号时生成 token
    """
    def create(self, **kwargs):
        obj = self.model(**kwargs)
        self._for_write = True
        obj.save(force_insert=True, using=self.db)
        return obj

    def create_from_api_result(self, kwargs):
        """
        用 API 结果创建对象
        """
        info = {}
        info['appid'] = kwargs['authorization_info']['authorizer_appid']
        info['alias'] = kwargs['authorizer_info']['alias']
        info['user_name'] = kwargs['authorizer_info']['user_name']
        info['head_img'] = kwargs['authorizer_info']['head_img']
        info['nick_name'] = kwargs['authorizer_info']['nick_name']
        info['qrcode_url'] = kwargs['authorizer_info']['qrcode_url']
        info['service_type'] = kwargs['authorizer_info']['service_type_info']['id']  # flake8 noqa
        info['verify_type'] = kwargs['authorizer_info']['verify_type_info']['id']  # flake8 noqa
        info['authorized'] = True
        return self.create(**info)
