# Real company photos downloader

Ce pack ne contient **pas** les photos elles-mêmes.
Il contient un script qui télécharge **de vraies photos existantes** depuis Wikimedia Commons
et construit automatiquement le dossier attendu par ton jeu :

company_realistic_assets/
  shipping/
    ships/
    containers/
    ports/
  airline/
    planes/
    crews/
    lounges/
  megabank/
    advisors/
    research/
    premium/
  energy/
    panels/
    grid/
    storage/
  defense/
    engineers/
    lines/
    contracts/

## Utilisation

1. Dézippe ce dossier.
2. Ouvre le Terminal dans ce dossier.
3. Lance :

```bash
python3 download_real_company_photos.py
```

4. Quand c'est fini, mets dans ton repo :
- `index.html`
- le dossier `company_realistic_assets/`

## Notes

- Le script essaie de récupérer **5 vraies images** par type d'amélioration.
- Il filtre les résultats pour éviter au maximum les schémas, logos, dessins, cartes et images hors-sujet.
- Un fichier `credits.json` est généré pour garder la source et la licence de chaque image.