# Nova Playlist

### Objectif
Avoir une playlist à jour dans un dossier DropBox avec les titres les plus joués sur Radio Nova sur une période donnée

### Requirements
- Python 2.7
- `youtube-dl`
- `beautifulsoup4`
- `dropbox_uploader.sh` (suivre la procédure d'installation d'une app DropBox)
- `eyed3`
- `requests`
- `requests_cache`

### Exemples d'utilisation
Sans caching en regardant les 3 derniers jours:
    python update.py --lookback 259200 --titles 20
Avec caching en regardant les 7 derniers jours:
    python update.py --lookback 604800 --titles 20 --workspace /tmp/toto

### `update.py`
- récupère la playlist de diffusion (scrap de Nova depuis un timestamp donné)
- crée la nouvelle playlist (simple compte des occurrences)
- scrape YouTube pour trouver les chansons (approximation que le premier résultat de la recherche est le bon)
- efface les anciens et récupére les nouveaux .mp3 avec `youtube-dl`
- tague automatiquement un mp3 avec artiste & titre
- construit un fichier de playlist
- met à jour le dossier DropBox

### Pour le téléphone
Il est possible d'automatiser la mise à jour du dossier sur téléphone, ainsi que le téléchargement pour accèder aux fichiers offlines, à l'aide de l'application DropSync
