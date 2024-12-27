"""
Description: 日志配置文件，用于配置日志管理系统
    
-*- Encoding: UTF-8 -*-
@File     ：log_config.py.py
@Author   ：King Songtao
@Time     ：2024/12/26 下午9:12
@Contact  ：king.songtao@gmail.com
"""
from configs.settings import *

# 实例化全局参数配置
param = BaseConfig()
log_directory = Path(param.LOG_DIRECTORY)

# 检查日志存放目录是否存在，不存在则创建
if not log_directory.exists():
    log_directory.mkdir(parents=True, exist_ok=True)

# 通过环境变量获取日志级别，默认为INFO
log_level = os.getenv("LOG_LEVEL", "INFO")

# 配置日志的格式
# log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: 8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
# 配置一个日志处理器，用于将日志信息输出到文件中
logger.add(
    log_directory / "llm_demos_{time:YYYY-MM-DD_HH-MM}.log",
    rotation="2 hours",
    retention="10 days",
    compression="zip",
    level=log_level,
    format=log_format,
    enqueue=True
)
