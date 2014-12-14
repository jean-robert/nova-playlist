# Nova Playlist

### Objectif
Avoir une playlist à jour dans un dossier DropBox avec les titres les plus joués sur Radio Nova sur une période donnée

### Requirements
- Python 2.7
- `youtube-dl`
- `dropbox_uploader.sh` (suivre la procédure d'installation d'une app DropBox)

### Settings
Configurable dans `settings.py`
- `LOOKBACK` la période sur laquelle compter les diffusions
- `NB_TITLES` le nombre de titres à sélectionner pour la playlist

### `update.py`
- récupère la playlist de diffusion (scrap de Nova depuis un timestamp donné)
- crée la nouvelle playlist (simple compte des occurrences)
- scrape YouTube pour trouver les chansons (approximation que le premier résultat de la recherche est le bon)
- efface les anciens et récupére les nouveaux .mp3 avec `youtube-dl`
- construit un fichier de playlist
- met à jour le dossier DropBox

### Pour le téléphone
Il est possible d'automatiser la mise à jour du dossier sur téléphone, ainsi que le téléchargement pour accèder aux fichiers offlines, à l'aide de l'application DropSync
