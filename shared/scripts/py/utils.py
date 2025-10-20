import logging
import sys

class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG':    '\033[36m',    # 青色
        'INFO':     '\033[32m',    # 绿色
        'WARNING':  '\033[33m',    # 黄色
        'ERROR':    '\033[31m',    # 红色
        'CRITICAL': '\033[35m',    # 紫红
    }
    RESET = '\033[0m'

    def format(self, record):
        log_msg = super().format(record)
        if record.levelname in self.COLORS and sys.stderr.isatty():
            return f"{self.COLORS[record.levelname]}{log_msg}{self.RESET}"
        return log_msg


def get_logger(name=None):
    """
    获取统一配置的日志器。
    - 如果 name 为 None，默认使用调用模块的 __name__
    - 自动避免重复配置
    """
    if name is None:
        # 自动获取调用者的模块名（需要 inspect）
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals['__name__']

    logger = logging.getLogger(name)
    
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = ColoredFormatter(
        fmt='[%(asctime)s] %(name)s:%(lineno)d %(levelname)-8s — %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)

    logger.addHandler(console_handler)

    return logger
