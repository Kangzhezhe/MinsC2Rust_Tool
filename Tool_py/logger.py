import logging
import os

# 创建一个自定义的日志处理器
class PrintAndFileHandler(logging.Handler):
    def __init__(self, filename):
        super().__init__()
        self.file_handler = logging.FileHandler(filename)
        self.console_handler = logging.StreamHandler()

    def emit(self, record):
        # 将日志消息写入文件
        self.file_handler.emit(record)
        # 将日志消息打印到控制台
        if 'DEBUG' in os.environ:
            self.console_handler.emit(record)

def logger_init(log_name='app.log'):
    # 配置日志记录
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # 创建并添加自定义的日志处理器
    handler = PrintAndFileHandler(log_name)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

# logger = logger_init()