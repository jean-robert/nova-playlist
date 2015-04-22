import requests
import urllib

from logorigins import logger

class YouTubeAPI(object):
    clientID = 'CLIENTID'
    clientSecret = 'CLIENTSECRET'
    refreshToken = 'REFRESHTOKEN'
    accessToken = None

    def get_access_token(self):
        payload = {'client_id': self.clientID,
                   'client_secret': self.clientSecret,
                   'refresh_token': self.refreshToken,
                   'grant_type': 'refresh_token'}
        r = requests.post('https://accounts.google.com/o/oauth2/token', data=payload)
        self.accessToken = r.json()['access_token']

    def search_youtube_id(self, title):
        try:
            if not self.accessToken:
                self.get_access_token()
            headers = {'Authorization':  'Bearer ' + self.accessToken}
            url = 'https://www.googleapis.com/youtube/v3/search'
            r = requests.get(url, params={'part': 'snippet',
                                          'q': title,
                                          'type': 'video'}, headers=headers)
            items = r.json()['items']
            if len(items) == 0:
                youtube_id = None
                logger.warning("No video found for %s" % title)
            else:
                youtube_id = items[0]['id']['videoId']
                logger.info("Found %s for song %s" % (youtube_id, title))
            return youtube_id
        except:
            logger.warning('YouTube API search error, fallback on scraper')
            return self.scrap_youtube_id(title)


    def scrap_youtube_id(self, title):
        url = "http://www.youtube.com/results?search_query=%s" % urllib.quote_plus(title)
        page = requests.get(url, timeout=15)

        if 'Aucune vid' in page.content:
            logger.warning("No video found for %s" % str(self))
            return None
        else:
            youtube_id = re.findall('href="\/watch\?v=(.*?)[&;"]', page.content)[0]
            logger.info("Found %s for song %s" % (youtube_id, str(self)))
            return youtube_id
