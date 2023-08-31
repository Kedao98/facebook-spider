import json
import time
from dataclasses import asdict, dataclass

from loguru import logger
from lxml import etree
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

from browser import Browser
from libs.utils import print_runtime, try_catch


@dataclass
class PostParsedResult:
    # 用户相关
    user_home_page: str = ''
    user_name: str = ''
    user_profile: str = ''
    user_followers_count: str = ''

    # 帖子相关
    content: str = ''
    post_url: str = ''
    img_links: list = None
    likes: str = ''
    comments: str = ''
    shares: str = ''

    create_time: str = ''

    def to_dict(self):
        return asdict(self)

    def to_json(self, indent=None):
        return json.dumps(self.to_dict(), indent=indent)

    def keys(self) -> list:
        return list(self.to_dict().keys())

    def values(self):
        return self.to_dict().values()

    def __str__(self):
        return self.to_json(2)


class PostsParser:
    def __init__(self, browser: Browser):
        self.browser = browser

    @print_runtime(True)
    def parse_all(self, post_xpath: str) -> PostParsedResult:
        post = self.browser.find_element(By.XPATH, post_xpath)

        self.browser.core_driver.execute_script('arguments[0].scrollIntoView();', post)
        self.browser.core_driver.execute_script('window.scrollBy(0,-100)')
        time.sleep(5)

        user_info = self.parse_user(post_xpath)

        return PostParsedResult(**user_info,
                                post_url=self.parse_post_url(post_xpath),
                                content=self.parse_content(post_xpath),
                                img_links=self.parse_img_link(post_xpath),
                                likes=self.parse_likes_count(post_xpath),
                                comments=self.parse_comments_count(post_xpath),
                                shares=self.parse_shares_count(post_xpath),
                                create_time=self.parse_create_time(post_xpath))

    @print_runtime()
    @try_catch(default=dict())
    def parse_user(self, post_xpath: str) -> dict:
        @try_catch(default='')
        def get_name(xpath):
            return self.browser.find_element(By.XPATH, xpath + '//a[@aria-label]').get_attribute('aria-label')

        @try_catch(default='')
        def get_profile(xpath):
            profile_parent_xpath = xpath + '//a[@aria-label]'
            html = etree.HTML(self.browser.find_element(By.XPATH, profile_parent_xpath).get_attribute('innerHTML'))
            return html.xpath('//image')[0].get('xlink:href')

        @try_catch(default='0')
        def get_followers_count(xpath):
            followers_xpath = xpath + '//a[@href and contains(text(), "Followers")]'
            return self.browser.find_element(By.XPATH, followers_xpath).text.replace(' Followers', '')

        @print_runtime()
        @try_catch(default='')
        def get_home_page(xpath):
            return self.browser.find_element(By.XPATH, xpath + '//a[@aria-label]').get_attribute('href')

        # 定位用户模块
        user_xpath = post_xpath + '//a[@aria-label]'
        self.browser.wait_unit(By.XPATH, user_xpath)
        user = self.browser.find_element(By.XPATH, user_xpath)

        # 浮窗显示
        ActionChains(self.browser.core_driver).move_to_element(user).perform()

        # 获取结果
        floating_window_xpath = '//div[@class="__fb-light-mode"]'
        self.browser.wait_unit(By.XPATH, floating_window_xpath + '//a[@aria-label]')
        user_info = dict(user_home_page=get_home_page(floating_window_xpath), user_name=get_name(floating_window_xpath),
                         user_profile=get_profile(floating_window_xpath),
                         user_followers_count=get_followers_count(floating_window_xpath))

        # 鼠标移动
        ActionChains(self.browser.core_driver).move_to_element_with_offset(user, -100, -100).perform()
        return user_info

    @print_runtime()
    @try_catch(default='')
    def parse_post_url(self, post_xpath: str) -> str:
        return self.browser.find_element(By.XPATH, post_xpath + '//span[@id]//a').get_attribute('href')

    @print_runtime()
    @try_catch(default='')
    def parse_create_time(self, post_xpath: str) -> str:

        # 定位时间模块
        time_button_xpath = post_xpath + '//span[@id]//a[contains(@href, "www.facebook.com") or @href="#"]'
        self.browser.wait_unit(By.XPATH, time_button_xpath, 5)
        time_button = self.browser.find_element(By.XPATH, time_button_xpath)

        # 浮窗显示
        ActionChains(self.browser.core_driver).move_to_element(time_button).perform()

        # 获取结果
        self.browser.wait_unit(By.CSS_SELECTOR, '[class="__fb-dark-mode"]')
        create_time = self.browser.find_element(By.CSS_SELECTOR, '[class="__fb-dark-mode"]').text

        # 鼠标移动
        ActionChains(self.browser.core_driver).move_to_element_with_offset(time_button, 100, 100).perform()
        return create_time

    @print_runtime()
    @try_catch(default='')
    def parse_content(self, post_xpath: str) -> str:
        try:
            self.browser.find_element(By.XPATH, post_xpath + '//*[text()="See more"]').click()
        except NoSuchElementException:
            logger.debug('`See more` button not found')
        msg = self.browser.find_element(By.XPATH, post_xpath + '//div[starts-with(@id, ":r")]/div').text
        return msg

    @try_catch(default=None)
    def parse_img_link(self, post_xpath: str) -> list:
        img_link_xpath = post_xpath + '//div[starts-with(@id, ":r")]//a[contains(@href, "www.facebook.com/photo")]'
        elements = self.browser.find_elements(By.XPATH, img_link_xpath)
        images = [element.get_attribute('href') for element in elements]
        return images

    @try_catch(default='0')
    def parse_likes_count(self, post_xpath: str) -> str:
        comments_toolbar_xpath = post_xpath + '//span[@role="toolbar"]/..'
        return self.browser.find_element(By.XPATH, comments_toolbar_xpath + '//span[text()]').text

    @try_catch(default='0')
    def parse_comments_count(self, post_xpath: str) -> str:
        comments_toolbar_xpath = post_xpath + '//span[@role="toolbar"]/../..'
        comments_xpath = comments_toolbar_xpath + '//span[ends-with(text(), " comments")]'
        comments = self.browser.find_element(By.XPATH, comments_xpath).text
        return comments.replace(' comments', '')

    @try_catch(default='0')
    def parse_shares_count(self, post_xpath: str) -> str:
        comments_toolbar_xpath = post_xpath + '//span[@role="toolbar"]/../..'
        shares_xpath = comments_toolbar_xpath + '//span[ends-with(text(), " shares")]'
        shares = self.browser.find_element(By.XPATH, shares_xpath).text
        return shares.replace(' shares', '')
