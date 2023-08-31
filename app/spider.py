import os
import time

from loguru import logger
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from app.parser import PostsParser, PostParsedResult
from browser import Browser
from libs.utils import print_runtime, download_chromedriver


def record_post(result: PostParsedResult, save_path: str = os.getenv('SPIDER_SAVE_PATH', '')) -> None:
    default_save_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'post_result.csv')
    save_path = save_path if save_path else default_save_path

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'a') as f:
        f.write(result.to_json() + '\n')


class FacebookSpider:
    home_page = 'https://www.facebook.com/search/posts/?q={keyword}'

    def __init__(self, user: str, password: str, driver_path: str = '', headless: bool = True):
        path = driver_path if driver_path else download_chromedriver('./')
        self.user, self.password = user, password
        self.browser = Browser(path, headless)
        self.parse = PostsParser(self.browser)

    @print_runtime()
    def open_home_page(self, keyword='homepage'):
        """
        打开Facebook主页
        :param keyword:
        :return:
        """
        self.browser.open_new_page('data:,')
        self.browser.close_all_pages()
        self.browser.open_new_page(self.home_page.format(keyword=keyword))

    @print_runtime()
    def login_account(self, user, password):
        """
        登录账号
        :param user:
        :param password:
        :return:
        """
        user_element, password_element = {'by': 'id', 'value': 'email'}, {'by': 'id', 'value': 'pass'}
        time.sleep(5)
        self.browser.wait_unit(**user_element)
        self.browser.insert_value(user, user_element)
        self.browser.insert_value(password, password_element)
        self.browser.find_element('id', 'loginbutton').click()

    @print_runtime()
    def search_keyword(self, keyword: str):
        """
        搜索关键词
        :param keyword: str
        :return:
        """
        self.browser.wait_unit(By.CSS_SELECTOR, '[aria-label="Facebook"]')
        self.browser.close_all_pages()
        self.browser.open_new_page(self.home_page.format(keyword=keyword))

        # 切换到最近posts
        self.browser.wait_unit(By.XPATH, '//div[@role="listitem"]//input[@dir="ltr" and @type="checkbox"]', 60)
        self.browser.click_element(By.XPATH, '//div[@role="listitem"]//input[@dir="ltr" and @type="checkbox"]')

    def crawl_posts(self):
        """
        获取帖子内容
        :return: PostParsedResult
        """
        for i in range(1, int(1e5)):
            # 滑动到可见位置
            self.browser.insert_key(Keys.SPACE, {'by': 'tag name', 'value': 'body'})

            post_xpath = f'//div[@role="feed"]/div[{i}]'
            if self.browser.wait_unit(By.XPATH, post_xpath):
                yield self.parse.parse_all(post_xpath)

            elif self.browser.wait_unit(By.XPATH, '//span[@dir="auto" and contains(text(), "End")]'):
                break

    def search(self, keyword, max_posts: int = 100):
        try:
            self.open_home_page(keyword)
            self.login_account(self.user, self.password)
            self.search_keyword(keyword)
            logger.warning('暂停等待加载')
            time.sleep(60)

            for i in range(max_posts):
                logger.info(f'parse post: {i + 1} / {max_posts}')
                record_post(next(self.crawl_posts()))
            logger.success('process finish')
        finally:
            self.browser.close_browser()


if __name__ == '__main__':
    chromedriver = download_chromedriver('./chromedriver')
    spider = FacebookSpider(user='', password='',
                            driver_path=chromedriver, headless=True)
    spider.search('huawei', max_posts=10)
