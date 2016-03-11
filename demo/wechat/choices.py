#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from wechat import consts

#=============================================================================
# 公众号类型
#=============================================================================
WECHAT_TYPE_CHOICES = (
    (consts.WECHAT_TYPE_SUB, '订阅号'),
    (consts.WECHAT_TYPE_SUB2, '升级后的订阅号'),
    (consts.WECHAT_TYPE_SERVICE, '服务号'),
)


#=============================================================================
# 公众号认证类型
#=============================================================================
VERIFY_TYPE_CHOICES = (
    (consts.VERIFY_TYPE_NONE, '未认证'),
    (consts.VERIFY_TYPE_WECHAT, '微信认证'),
    (consts.VERIFY_TYPE_WEIBO, '新浪微博认证'),
    (consts.VERIFY_TYPE_TENCENT_WEIBO, '腾讯微博认证'),
    (consts.VERIFY_TYPE_BASE_VERIFY, '已资质认证通过但还未通过名称认证'),
    (consts.VERIFY_TYPE_3_1, '已资质认证通过、还未通过名称认证，但通过了新浪微博认证'),
    (consts.VERIFY_TYPE_3_2, '已资质认证通过、还未通过名称认证，但通过了腾讯微博认证'),
)
