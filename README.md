# attestaFion
AttestaFion, le générateur d'attestations COVID (pas comme les autres)

**Avertissement: Cet outil n'a pas pour vocation à vous dispenser des restrictions COVID.**
Cela dit il pourrait vous éviter de payer le prix fort une petite étourderie.

Toutefois, le fonctionnement même du générateur d'autorisations officiel soulève quelques questions... :

En essayant d'antidater une attestation obtenue via :
https://media.interieur.gouv.fr/attestation-deplacement-derogatoire-covid-19/

On constate qu'il n'existe pas de validation dans le formulaire pour empêcher de déclarer une heure passée...
Par contre, le QRcode généré lui, mentionne bien l'heure déclarée, AINSI QUE, l'heure de la génération de l'attestation...
Ainsi, au moment du contrôle une bien mauvaise surprise vous attends... Pas cool.

Voici donc un serveur qui utilise la meme addresse que ci dessus mais qui va "corriger" le QRcode afin de couvrir votre Fion...

Disponible ici :
# https://attestafion-a4j2wdhiza-nw.a.run.app/

# Usage
Naviguez vers l'adresse ci dessus.

Renseignez vos données ainsi qu'une durée de délai (par exemple il est 16h, si vous renseignez un délai de 42 minutes, l'attestation générée présentera une heure de 15h18).

Profitez de la liberté !

## Le serveur ne conserve aucune donnée ni attestation !

Si vous souhaitez héberger vous meme le service:
# Installation Docker (recommandée)
```
docker build -t attestafion .
docker run -p 8080:8080 attestafion
```

# Installation manuelle
Installer les dépendances:
```
pip install -r requirements.txt
```

Installer Firefox et geckodriver:
```
https://download-installer.cdn.mozilla.net/pub/firefox/releases/86.0.1/linux-x86_64/en-US/firefox-86.0.1.tar.bz2
https://github.com/mozilla/geckodriver/releases/download/v0.29.0/geckodriver-v0.29.0-linux64.tar.gz
(ce dernier doir être ajouté au $PATH)
```

Démarrez le serveur:
```
python attestaFion.py
```
(ou bien, si gunicorn est installé : 
```gunicorn attestaFion:app --workers 1 --threads 1 --timeout 0 -b 0.0.0.0:8080```
)