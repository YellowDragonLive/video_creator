"""Seedance Studio — 日志管理核心"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

import config

def setup_logger(name: str = 'SeedanceStudio'):
    """
    配置并返回一个日志器实例。
    支持：控制台彩色输出、文件持久化、分级记录。
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # 如果已经有 handler，不再添加（防止重复输出）
    if logger.handlers:
        return logger

    # 1. 确保日志目录存在
    os.makedirs(config.LOGS_DIR, exist_ok=True)

    # 2. 格式化定义
    # 控制台格式 (简短、清晰)
    console_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    # 文件格式 (详细、包含完整日期)
    file_formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] [%(filename)s:%(lineno)d]: %(message)s'
    )

    # 3. 控制台 Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    # 4. 文件 Handler (支持按大小切割，保留 5 个历史版本)
    file_handler = RotatingFileHandler(
        config.LOG_FILE,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    return logger

# 预创建默认日志器
logger = setup_logger()
