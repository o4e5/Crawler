import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementNotVisibleException, StaleElementReferenceException
import platform
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os.path as osp


class CollectLinks:
    def __init__(self, no_gui=False, proxy=None):
        executable = ''

        if platform.system() == 'Windows':
            print('감지된 운영체제 : Windows NT')
            executable = './chromedriver/chromedriver_win.exe'
        elif platform.system() == 'Linux':
            print('감지된 운영체제 : Linux')
            executable = './chromedriver/chromedriver_linux'
        elif platform.system() == 'Darwin':
            print('감지된 운영체제 : MacOS')
            executable = './chromedriver/chromedriver_mac'
        else:
            raise OSError('올바르지 않은 운영체제 타입')

        if not osp.exists(executable):
            raise FileNotFoundError('ChromeDriver 파일은 다음 위치에 있어야 합니다 : {}'.format(executable))

        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        if no_gui:
            chrome_options.add_argument('--headless')
        if proxy:
            chrome_options.add_argument("--proxy-server={}".format(proxy))
        self.browser = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=chrome_options)

        browser_version = '버전 감지 실패함'
        chromedriver_version = '버전 감지 실패함'
        major_version_different = False

        if 'browserVersion' in self.browser.capabilities:
            browser_version = str(self.browser.capabilities['browserVersion'])

        if 'chrome' in self.browser.capabilities:
            if 'chromedriverVersion' in self.browser.capabilities['chrome']:
                chromedriver_version = str(self.browser.capabilities['chrome']['chromedriverVersion']).split(' ')[0]

        if browser_version.split('.')[0] != chromedriver_version.split('.')[0]:
            major_version_different = True

        print('_________________________________')
        print('현재 웹 브라우저 버전 :\t{}'.format(browser_version))
        print('현재 ChromeDriver 버전 :\t{}'.format(chromedriver_version))
        if major_version_different:
            print('경고 : ChromeDriver 버전과 웹 브라우저 버전이 다릅니다.')
            print(
                '"http://chromedriver.chromium.org/downloads"에서 올바른 버전을 다운로드하고 "./chromedriver"에 배치합니다.')
        print('_________________________________')

    def get_scroll(self):
        pos = self.browser.execute_script("return window.pageYOffset;")
        return pos

    def wait_and_click(self, xpath):
        try:
            w = WebDriverWait(self.browser, 15)
            elem = w.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            elem.click()
            self.highlight(elem)
        except Exception as e:
            print('클릭 시간 초과 - {}'.format(xpath))
            print('브라우저 새로고침 중 . .')
            self.browser.refresh()
            time.sleep(2)
            return self.wait_and_click(xpath)

        return elem

    def highlight(self, element):
        self.browser.execute_script("arguments[0].setAttribute('style', arguments[1]);", element,
                                    "background: yellow; border: 2px solid red;")

    @staticmethod
    def remove_duplicates(_list):
        return list(dict.fromkeys(_list))

    def google(self, keyword, add_url=""):
        self.browser.get("https://www.google.com/search?q={}&source=lnms&tbm=isch{}".format(keyword, add_url))

        time.sleep(1)

        print('정보 수집 중 . . .')

        elem = self.browser.find_element_by_tag_name("body")

        for i in range(60):
            elem.send_keys(Keys.PAGE_DOWN)
            time.sleep(0.2)

        try:
            self.wait_and_click('//input[@type="button"]')

            for i in range(60):
                elem.send_keys(Keys.PAGE_DOWN)
                time.sleep(0.2)

        except ElementNotVisibleException:
            pass

        photo_grid_boxes = self.browser.find_elements(By.XPATH, '//div[@class="bRMDJf islir"]')

        print('링크 정보 수집 중')

        links = []

        for box in photo_grid_boxes:
            try:
                imgs = box.find_elements(By.TAG_NAME, 'img')

                for img in imgs:
                    src = img.get_attribute("src")
                    if str(src).startswith('data:'):
                        src = img.get_attribute("data-iurl")
                    links.append(src)

            except Exception as e:
                print('[Google에서 링크를 수집하는 동안 예외가 발생했습니다.] {}'.format(e))

        links = self.remove_duplicates(links)

        print('링크 수집 완료 : 사이트 : {}, 키워드 : {}, 모두 : {}'.format('google', keyword, len(links)))
        self.browser.close()

        return links

    def naver(self, keyword, add_url=""):
        self.browser.get(
            "https://search.naver.com/search.naver?where=image&sm=tab_jum&query={}{}".format(keyword, add_url))

        time.sleep(1)

        print('정보 수집 중 . . .')

        elem = self.browser.find_element_by_tag_name("body")

        for i in range(60):
            elem.send_keys(Keys.PAGE_DOWN)
            time.sleep(0.2)

        imgs = self.browser.find_elements(By.XPATH,
                                          '//div[@class="photo_bx api_ani_send _photoBox"]//img[@class="_image _listImage"]')

        print('정보 수집 중 . . .')

        links = []

        for img in imgs:
            try:
                src = img.get_attribute("src")
                if src[0] != 'd':
                    links.append(src)
            except Exception as e:
                print('[Naver에서 링크를 수집하는 동안 예외가 발생했습니다. ] {}'.format(e))

        links = self.remove_duplicates(links)

        print('링크 수집 완료 : 사이트 : {}, 키워드 : {}, 모두 : {}'.format('naver', keyword, len(links)))
        self.browser.close()

        return links

    def google_full(self, keyword, add_url=""):
        print('[전체 해상도 모드]')

        self.browser.get("https://www.google.com/search?q={}&tbm=isch{}".format(keyword, add_url))
        time.sleep(1)

        elem = self.browser.find_element_by_tag_name("body")

        print('정보 수집 중 . . .')

        self.wait_and_click('//div[@data-ri="0"]')
        time.sleep(1)

        links = []
        count = 1

        last_scroll = 0
        scroll_patience = 0

        while True:
            try:
                xpath = '//div[@id="islsp"]//div[@class="v4dQwb"]'
                div_box = self.browser.find_element(By.XPATH, xpath)
                self.highlight(div_box)

                xpath = '//img[@class="n3VNCb"]'
                img = div_box.find_element(By.XPATH, xpath)
                self.highlight(img)

                xpath = '//div[@class="k7O2sd"]'
                loading_bar = div_box.find_element(By.XPATH, xpath)

                while str(loading_bar.get_attribute('style')) != 'display: none;':
                    time.sleep(0.1)

                src = img.get_attribute('src')

                if src is not None:
                    links.append(src)
                    print('%d: %s' % (count, src))
                    count += 1

            except StaleElementReferenceException:
                pass
            except Exception as e:
                print('[google_full에서 링크를 수집하는 동안 예외가 발생했습니다.] {}'.format(e))

            scroll = self.get_scroll()
            if scroll == last_scroll:
                scroll_patience += 1
            else:
                scroll_patience = 0
                last_scroll = scroll

            if scroll_patience >= 30:
                break

            elem.send_keys(Keys.RIGHT)

        links = self.remove_duplicates(links)

        print('링크 수집 완료 : 사이트 : {}, 키워드 : {}, 모두 : {}'.format('google_full', keyword, len(links)))
        self.browser.close()

        return links

    def naver_full(self, keyword, add_url=""):
        print('[전체 해상도 모드]')

        self.browser.get(
            "https://search.naver.com/search.naver?where=image&sm=tab_jum&query={}{}".format(keyword, add_url))
        time.sleep(1)

        elem = self.browser.find_element_by_tag_name("body")

        print('정보 수집 중 . .')

        self.wait_and_click('//div[@class="photo_bx api_ani_send _photoBox"]')
        time.sleep(1)

        links = []
        count = 1

        last_scroll = 0
        scroll_patience = 0

        while True:
            try:
                xpath = '//div[@class="image _imageBox"]/img[@class="_image"]'
                imgs = self.browser.find_elements(By.XPATH, xpath)

                for img in imgs:
                    self.highlight(img)
                    src = img.get_attribute('src')

                    if src not in links and src is not None:
                        links.append(src)
                        print('%d: %s' % (count, src))
                        count += 1

            except StaleElementReferenceException:
                pass
            except Exception as e:
                print('[naver_full에서 링크를 수집하는 중 예외가 발생했습니다.] {}'.format(e))

            scroll = self.get_scroll()
            if scroll == last_scroll:
                scroll_patience += 1
            else:
                scroll_patience = 0
                last_scroll = scroll

            if scroll_patience >= 100:
                break

            elem.send_keys(Keys.RIGHT)
            elem.send_keys(Keys.PAGE_DOWN)

        links = self.remove_duplicates(links)

        print('링크 수집 완료 : 사이트 : {}, 키워드 : {}, 모두 : {}'.format('naver_full', keyword, len(links)))
        self.browser.close()

        return links


if __name__ == '__main__':
    collect = CollectLinks()
    links = collect.naver_full('Example')
    print(len(links), links)