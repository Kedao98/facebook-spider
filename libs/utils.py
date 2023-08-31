import time
from functools import wraps

from loguru import logger
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.driver_cache import DriverCacheManager


def print_runtime(print_return=False):
    def deco(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            t0 = time.time()
            result = func(*args, **kwargs)
            t1 = time.time()
            delta = t1 - t0
            logger.info(f'{func.__name__} run time[s]: {delta:.3f}')
            if print_return:
                logger.info(f'{func.__name__} return: {result}')
            return result

        return wrapper

    return deco


def try_catch(default=None):
    def deco(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception:
                return default

        return wrapper

    return deco


def download_chromedriver(path: str) -> str:
    cache_manager = DriverCacheManager(root_dir=path)
    driver_path = ChromeDriverManager(cache_manager=cache_manager).install()
    return driver_path
