import json
import re
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


    def clean_channel_playlist(self, playlist_id):
        if not self.accessToken:
            self.get_access_token()
        headers = {'Authorization':  'Bearer ' + self.accessToken}
        url = 'https://www.googleapis.com/youtube/v3/playlistItems'
        r = requests.get(url, params={'part': 'snippet',
                                      'playlistId': playlist_id,
                                      'maxResults': 50}, headers=headers)
        for video in r.json()['items']:
            vd = requests.delete(url, params={'id': video['id']}, headers=headers)
            if vd.status_code != 204:
                logger.error("Error removing song from playlist %s" % (vd.text))


    def build_channel_playlist(self, playlist_id, songs):
        if not self.accessToken:
            self.get_access_token()
        url = 'https://www.googleapis.com/youtube/v3/playlistItems?part=snippet'
        headers = {'Authorization':  'Bearer ' + self.accessToken,
                   'Content-Type': 'application/json'}
        songPosition = -1
        for song in songs:
            if song.youtube_id:
                songPosition += 1
                payload = json.dumps({'snippet':
                                      {
                                          'playlistId': playlist_id,
                                          'resourceId': {
                                              'kind': 'youtube#video',
                                              'videoId': song.youtube_id
                                          },
                                          'position': songPosition
                                      }
                                  })
                logger.debug('Sending payload %s' % (payload))
                r = requests.post(url, data=payload, headers=headers)
                if r.status_code != 200:
                    logger.error("Error publishing %s : %s" % (song.artist + ' / ' + song.title, r.text))
