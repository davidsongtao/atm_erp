"""
Description: 项目全局配置文件，用于配置项目中的参数
    
-*- Encoding: UTF-8 -*-
@File     ：settings.py.py
@Author   ：King Songtao
@Time     ：2024/12/26 下午8:24
@Contact  ：king.songtao@gmail.com
"""
from loguru import logger
import os
from pathlib import Path


class BaseConfig(object):
    def __init__(self):
        # 数据库配置信息
        self.DATABASE_SETTING = {
            'host': "localhost",
            'user': "root",
            'password': "",
            'database': "order_management",
            'port': 3306
        }

        # 日志相关配置信息
        self.LOG_DIRECTORY = "logs"

        # 自定义员工管理页账户信息表头
        self.CUSTOM_HEADER = {
            "id": "账户编号",
            "username": "登录账号",
            "password": "登录密码",
            "role": "角色权限",
            "name": "用户名",
        }
