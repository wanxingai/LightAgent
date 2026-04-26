#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
作者: [weego/WXAI-Team]
最后更新: 2026-02-20
"""

import logging
import os
from typing import Any, Optional


class LoggerManager:
    """集中管理日志系统"""

    def __init__(self, name: str, debug: bool, log_level: str, log_file: Optional[str] = None):
        self.name = name
        self.debug = debug
        self.logger = self._setup_logger(log_level, log_file)
        self.traceid = ""

    def _setup_logger(self, log_level: str, log_file: Optional[str] = None) -> logging.Logger:
        logger = logging.getLogger(self.name)
        logger.setLevel(log_level.upper())
        logger.propagate = False

        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

        if self.debug:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        if log_file:
            # 确保 log 目录存在
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)

            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    def log(self, level: str, action: str, data: Any):
        """记录日志"""
        if not self.debug:
            return

        trace_info = f"[TraceID: {self.traceid}] " if self.traceid else ""
        log_message = f"{trace_info}{action}: {data}"
        safe_msg = log_message.encode('utf-8', 'ignore').decode('utf-8')

        if level == "DEBUG":
            self.logger.debug(safe_msg)
        elif level == "INFO":
            self.logger.info(safe_msg)
        elif level == "ERROR":
            self.logger.error(safe_msg)

    def set_traceid(self, traceid: str):
        """设置当前跟踪ID"""
        self.traceid = traceid
