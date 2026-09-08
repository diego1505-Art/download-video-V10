# DowFlow

DowFlow est une application locale Flask pour télécharger et regarder des médias depuis des URLs compatibles avec `yt-dlp`, lire des fichiers locaux, gérer des sous-titres, et lancer plusieurs téléchargements depuis une liste d'URLs.

L'interface principale est disponible sur :

```text
http://127.0.0.1:5001
```

## Fonctionnalités

- Téléchargement vidéo ou audio via `yt-dlp`.
- Choix de qualité vidéo : auto max, 2160p, 1440p, 1080p, 720p, 480p.
- Fusion audio/vidéo avec FFmpeg quand disponible.
- Accélération des téléchargements avec `aria2c` quand disponible.
- Lecture directe dans la page pour les formats compatibles navigateur.
- Lecture de fichiers locaux sans copie quand un chemin local est saisi.
- Sélection de fichiers locaux depuis l'interface.
- Support de sous-titres `.ass` et `.srt` côté lecteur.
- Téléchargement de plusieurs URLs depuis une fenêtre dédiée.
- Import d'un fichier `.txt`, `.list` ou `.csv` dans la liste d'URLs.
- Rangement automatique dans des sous-dossiers de `downloads`.
- Badge d'état FFmpeg dans l'interface.

## Structure Du Projet

```text
app.py                  Serveur Flask et routes HTTP
playlist.py             Orchestration du téléchargement yt-dlp
browser_extractor.py    Fallback navigateur Playwright générique
franime_extractor.py    Extracteur spécialisé existant dans le projet
config.py               Constantes partagées
utils.py                Helpers communs, dont FFmpeg et URLs HTTP
templates/dowload.html  Interface web complète
start.bat               Lancement Windows avec vérifications runtime
requirements.txt        Dépendances Python
extract_urls_from_txt.py Extraction d'URLs depuis un texte/JSON
url_collector.py        Script expérimental de collecte
downloads/              Dossier de sortie des médias
```

## Installation

Sur Windows, le plus simple est d'utiliser :

```powershell
.\start.bat
```

Le script :

- crée le virtualenv si nécessaire ;
- installe les dépendances Python ;
- vérifie Chromium pour Playwright ;
- vérifie `aria2c` ;
- ajoute FFmpeg au `PATH` de la session si l'installation Winget est trouvée ;
- lance le serveur sur `http://127.0.0.1:5001`.

Installation manuelle :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
python app.py
```

## Dépendances

Python :

```text
Flask
yt-dlp
playwright
requests
```

Outils externes recommandés :

- `ffmpeg` et `ffprobe` pour fusionner proprement vidéo + audio et convertir l'audio.
- `aria2c` pour accélérer les téléchargements fragmentés.
- Chromium Playwright pour les fonctions qui nécessitent un navigateur.

## Utilisation

### Télécharger Une URL

1. Colle une URL dans le champ principal.
2. Choisis `Audio` ou `Video`.
3. Choisis la qualité si tu télécharges une vidéo.
4. Clique sur `Telecharger`.

Si le fichier téléchargé est prévisualisable par le navigateur, il s'affiche dans le lecteur intégré.

### Lire Un Fichier Local

Deux méthodes sont possibles :

- clique sur `Choisir une video locale` ;
- ou colle un chemin local dans le champ principal.

Quand un chemin local est utilisé, le fichier est servi directement par l'application sans être recopié dans `downloads`.

### Ajouter Des Sous-Titres

Clique sur `Choisir un .ass ou .srt`, puis sélectionne ton fichier de sous-titres.

Le rendu `.ass` est interprété côté navigateur. Les timings et le texte sont pris en charge, mais les styles avancés ASS ne sont pas reproduits parfaitement.

### Télécharger Plusieurs URLs

1. Clique sur `URLs multiples`.
2. Colle une URL par ligne, ou importe un fichier `.txt`.
3. Clique sur `Telecharger la liste`.

La liste est traitée séquentiellement. Une erreur sur une URL n'arrête pas toute la série.

### Trouver Des Épisodes

La fenêtre `URLs multiples` contient aussi un bouton `Trouver episodes`.

Cette fonction prend la première URL de la liste, tente de trouver les saisons/épisodes disponibles, puis remplit la zone avec les URLs générées. C'est une fonction expérimentale : elle dépend de la structure de la page distante et peut échouer si le site change son HTML, son API ou bloque la requête.

## Rangement Des Téléchargements

Les fichiers sont enregistrés dans `downloads`.

Le rangement est automatique :

- YouTube va dans `downloads/youtube`.
- Les autres sources vont dans un dossier dérivé du domaine, du chemin, de l'ID éventuel et de la saison éventuelle.

Exemple :

```text
downloads/youtube/
downloads/example-com-serie-id-123-s-1/
```

## CLI

Le projet garde aussi un mode console :

```powershell
python playlist.py
```

Ce mode permet un téléchargement simple sans passer par l'interface web.

## Scripts Utilitaires

Extraire des URLs depuis un fichier texte ou JSON :

```powershell
python extract_urls_from_txt.py fichier.txt --output urls_extraites.txt
```

`url_collector.py` est un script expérimental. Il n'est pas nécessaire au fonctionnement principal de DowFlow.

## Limites Connues

- Le fichier [templates/dowload.html](templates/dowload.html) contient HTML, CSS et JavaScript dans un seul fichier. Il est fonctionnel, mais volumineux.
- Les fonctions basées sur Playwright peuvent être lentes au premier lancement.
- Les formats `.mkv`, `.avi`, `.mov` peuvent être acceptés localement, mais ne sont pas toujours lisibles par le lecteur HTML5.
- Une vidéo locale basse résolution restera floue en plein écran : l'application ne peut pas recréer des détails qui n'existent pas dans le fichier.
- Les sites tiers peuvent changer leur structure ou bloquer certaines requêtes, ce qui peut casser les fonctions expérimentales.

## Vérification Rapide

```powershell
python -c "import app, playlist, browser_extractor, franime_extractor, config, utils; print('ok')"
```

Si la commande affiche `ok`, les imports principaux fonctionnent.
