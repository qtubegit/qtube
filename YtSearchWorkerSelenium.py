from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions 
from selenium import webdriver

import urllib.parse

from YtSafeSignal import YtSafeSignal
from YtSearchWorker import YtSearchWorker
from YtTrack import YtTrack

class YtSearchWorkerSelenium(YtSearchWorker):
    options = Options()
    options.add_argument('--headless=new')
    driver = webdriver.Chrome(options=options)

    def __init__(self, query):
        super().__init__()
        self.query = query

    def search(self):
        searchUrl = f'https://www.youtube.com/results?search_query={self.query}'
        driver = YtSearchWorkerSelenium.driver
        driver.get(searchUrl)

        condition = expected_conditions.presence_of_element_located((By.TAG_NAME, 'body'))
        WebDriverWait(driver, 0).until(condition)
        videos = driver.find_elements(By.ID, "video-title")

        tracks = []
        for v in videos:
            href = v.get_attribute('href')
            if href is None: continue
            
            up = urllib.parse.urlparse(href)
            qs = urllib.parse.parse_qs(up.query)
            if 'v' not in qs: continue

            tags = { 'videoId': qs['v'][0] }
            track = YtTrack(v.text, **tags)
            tracks.append(track)

        YtSafeSignal.emit(self.tracksFound, tracks)

