# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import logging
from django.db import models
from wechat.utils import get_component
from wechat import consts
from wechat import choices
from wechat import managers


model_logger = logging.getLogger('django.db.wechat')


class Wechat(models.Model):
    """
    公众号
    """
    appid = models.CharField('公众号 ID', max_length=20, default='')
    alias = models.CharField('公众号名称', max_length=20, null=True, blank=True)
    service_type = models.IntegerField(
        '公众号类型', choices=choices.WECHAT_TYPE_CHOICES,
        default=consts.WECHAT_TYPE_SUB
    )
    nick_name = models.CharField('昵称', max_length=32, null=True, blank=True)
    head_img = models.URLField('头像', max_length=256, null=True, blank=True)
    user_name = models.CharField('内部名称', max_length=32)
    qrcode_url = models.URLField(
        '二维码URL', max_length=256, null=True, blank=True)
    authorized = models.BooleanField('授权')
    verify_type = models.PositiveIntegerField(
        '认证类型', choices=choices.VERIFY_TYPE_CHOICES)
    funcscope_categories = models.CommaSeparatedIntegerField(
        '权限集', max_length=64)
    join_time = models.DateTimeField('授权时间', auto_now_add=True)

    class Meta:
        get_latest_by = 'join_time'
        verbose_name = '公众号'
        verbose_name_plural = '公众号'

    def __unicode__(self):
        return '公众号 {0}'.format(self.alias)

    def __str__(self):
        return self.__unicode__().encode('utf-8')

    def is_valid(self):
        return self.authorized

    @property
    def client(self):
        component = get_component()
        return component.get_client_by_appid(self.appid)
