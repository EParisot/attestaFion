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

(à héberger vous-memes localement, à vous d'utiliser Gunicorn, WSGI, etc selon vos besoins !)

# instructions
Installer les dépendances:
```
pip install -r requirements.txt
```
### !!! Ce programme nécéssite Chrome 89 ainsi que chromedriver !!!
chromedriver :
```
wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/
```

Démarrez le serveur:
```
python attestaFion.py
```
(ou bien, si gunicorn est installé : ```./run.sh``` )

Naviguez vers localhost:8000 (ou votre ip publique, dans ce cas mappez le port correspondant à la machine qui heberge le serveur).

Renseignez vos données ainsi qu'une durée de délai (par exemple il est 16h, si vous renseignez un délai de 42 minutes, l'attestation générée présentera une heure de 15h18).

Profitez de la liberté !