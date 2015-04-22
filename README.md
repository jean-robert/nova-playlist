# Nova Playlist

[![Build Status](https://travis-ci.org/gtnx/nova-playlist.svg?branch=master)](https://travis-ci.org/gtnx/nova-playlist)

### Objectif
Avoir une playlist à jour dans un dossier DropBox avec les titres les plus joués sur Radio Nova sur une période donnée

### Requirements
- Python 2.7
- `youtube-dl`
- `beautifulsoup4`
- `dropbox_uploader.sh` (suivre la procédure d'installation d'une app DropBox)
- `mutagen`
- `mutagenerate`
- `requests`
- `requests_cache`

### Exemples d'utilisation
Sans caching en regardant les 3 dernières heures:

    python update.py --lookback 3h --titles 5

Avec caching en regardant les 7 derniers jours:

    python update.py --lookback 7d --titles 20 --workspace /tmp/toto

Strategy mostcommon: sont sélectionnés les morceaux les plus joués

    python update.py --lookback 7d --titles 20 --strategy mostcommon

Strategy random: sont sélectionnés des morceaux au hasard

    python update.py --lookback 7d --titles 20 --strategy random

Strategy mixed: 50% des morceaux sont choisis en mostcommon, 50% en random

    python update.py --lookback 7d --titles 20 --strategy mixed

Utilisation de la radio Fip:

    python update.py --lookback 7d --titles 20 --radio fip

Utilisation de la radio OuiFm:

    python update.py --lookback 7d --titles 20 --radio oui

Utilisation de l'API YouTube pour chercher les ids des vidéos

    python update.py --lookback 7d --titles 20 --youtube-id-source search

Upload vers une channel YouTube plutot que DropBox

    python update.py --lookback 7d --titles 20 --playlist-id PLtYGBipNVsCbhpMg70-mRG3iwzc2uUVeD



### `update.py`
- récupère la playlist de diffusion (scrap de Nova depuis un timestamp donné)
- crée la nouvelle playlist (simple compte des occurrences)
- scrape YouTube pour trouver les chansons (approximation que le premier résultat de la recherche est le bon)
- efface les anciens et récupére les nouveaux .mp3 avec `youtube-dl`
- tague automatiquement un mp3 avec artiste & titre
- construit un fichier de playlist
- met à jour le dossier DropBox ou update la playlist YouTube

### Pour le téléphone
Il est possible d'automatiser la mise à jour du dossier sur téléphone, ainsi que le téléchargement pour accèder aux fichiers offlines, à l'aide de l'application DropSync


### Pour configurer l'API YouTube
Suivre la procédure pour une ***Installed App*** ([voir ici](https://developers.google.com/youtube/v3/guides/authentication#installed-apps)), afin de récupérer le `clientId` et le `clientSecret`. On obtient dans un premier temps l'`authorizationCode` qui nécessite une validation à la main de l'utilisateur, puis on demande un premier `accessToken` qui sera fournit avec un `refreshToken` à conserver.


Concrètement :
```
GET https://accounts.google.com/o/oauth2/auth?
    scope=https://www.googleapis.com/auth/youtube&
    redirect_uri=urn:ietf:wg:oauth:2.0:oob&
    response_type=code&
    client_id=<CLIENT_ID>
```
fournit l'`authorizationCode`,
```
POST https://accounts.google.com/o/oauth2/token

code=<authorizationCode>&
client_id=<clientId>&
client_secret=<clientSecret>&
redirect_uri=urn:ietf:wg:oauth:2.0:oob&
grant_type=authorization_code
```
fournit l'`accessToken` avec le `refreshToken` que l'on conserve soigneusement. Lors de chaque update, on utilisera le refresh pour récupérer un nouveau token d'accès.
