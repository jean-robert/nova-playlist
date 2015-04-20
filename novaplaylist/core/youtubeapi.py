import requests

class ytapi(object):
    clientID = 'CLIENTID'
    clientSecret = 'CLIENTSECRET'
    refreshToken = 'REFRESHTOKEN'
    accessToken = None

    def getAccessToken(self):
        payload = {'client_id': self.clientID,
                   'client_secret': self.clientSecret,
                   'refresh_token': self.refreshToken,
                   'grant_type': 'refresh_token'}
        r = requests.post('https://accounts.google.com/o/oauth2/token', data=payload)
        self.accessToken = r.json()['access_token']

    def searchVideoId(self, title):
        if not self.accessToken:
            self.getAccessToken()
        headers = {'Authorization':  'Bearer ' + self.accessToken}
        url = 'https://www.googleapis.com/youtube/v3/search'
        r = requests.get(url, params={'part': 'snippet',
                                      'q': title,
                                      'type': 'video'}, headers=headers)
        items = r.json()['items']
        if len(items) == 0:
            return None
        return items[0]['id']['videoId']
