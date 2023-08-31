import json
import logging
from typing import List

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

logger = logging.getLogger(__name__)


class Browser:
    def __init__(self, path: str, headless: bool = True):
        self.path = path
        self.headless = headless

        self.core_driver = self.init_browser(path, headless)

    def restart(self) -> None:
        self.close_browser()
        self.core_driver = self.init_browser(self.path, self.headless)

    def init_browser(self, path: str, headless: bool) -> webdriver:
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-infobars")
        options.add_argument("start-maximized")
        options.add_argument("--disable-extensions")
        options.add_argument("--start-maximized")
        # options.add_argument('window-size=3000,2000')

        # Pass the argument 1 to allow and 2 to block
        options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 1
        })
        if headless:
            options.add_argument("--headless")
        return webdriver.Chrome(path, options=options, )

    def open_new_page(self, url: str) -> None:
        self.core_driver.switch_to.window(self.core_driver.window_handles[-1])
        # self.core_driver.delete_all_cookies()
        self.core_driver.execute_script(f'window.open("{url}");')
        self.core_driver.switch_to.window(self.core_driver.window_handles[-1])

    def close_all_pages(self) -> None:
        for _ in range(len(self.core_driver.window_handles) - 1):
            self.core_driver.switch_to.window(self.core_driver.window_handles[-1])
            self.core_driver.close()
        self.core_driver.switch_to.window(self.core_driver.window_handles[-1])

    def check_browser_status(self) -> None:
        try:
            self.core_driver.execute_script('javascript:void(0);')
        except Exception:
            self.close_browser()
            self.core_driver = self.init_browser(self.path, self.headless)

    def close_browser(self) -> None:
        self.core_driver.quit()

    def find_element(self, by: str, value: str) -> WebElement:
        return self.core_driver.find_element(by, value)

    def find_elements(self, by: str, value: str) -> List[WebElement]:
        return self.core_driver.find_elements(by, value)

    def click_element(self, by: str, value: str, ignore_error: bool = False) -> None:
        try:
            self.find_element(by, value).click()
        except NoSuchElementException:
            if not ignore_error:
                raise NoSuchElementException

    def insert_key(self, value: str, element: dict) -> None:
        button = self.core_driver.find_element(**element)
        button.send_keys(value)

    def insert_value(self, value: str, element: dict) -> None:
        button = self.core_driver.find_element(**element)
        js = 'arguments[0].removeAttribute("readonly");'
        self.core_driver.execute_script(js, button)
        button.clear()
        button.send_keys(value)

    def select_value(self, value: str, select_element: dict) -> None:
        select_button = Select(self.find_element(**select_element))
        if value:
            select_button.select_by_value(value)
        else:
            select_button.select_by_index(1)

    def wait_unit(self, by: str, value: str, timeout: float = 10) -> bool:
        try:
            WebDriverWait(self.core_driver, timeout, poll_frequency=0.5).until(
                EC.presence_of_element_located((by, value))
            )
            return True
        except Exception:
            return False

    def get_response_body(self, mark: str) -> str:
        result = ''
        for entry in self.core_driver.get_log('performance'):
            if mark not in entry['message']:
                continue
            response = json.loads(entry['message'])['message']
            request_id = response['params']['requestId']
            result = self.core_driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})['body']
            break
        return result

    def show_screenshot(self, screenshot_file='screen.png') -> None:
        self.core_driver.get_screenshot_as_file(screenshot_file)

    @property
    def url(self) -> str:
        return self.core_driver.current_url
