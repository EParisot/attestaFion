# attestaFion
AttestaFion, le générateur d'attestations COVID (pas comme les autres)

Avertissement: Cet outil n'a pas pour vocation à vous dispenser des restrictions COVID.
Cela dit il pourrait vous éviter de payer le prix fort une petite étourderie.

Toutefois, le fonctionnement même du générateur d'autorisations soulève quelques questions... :

En essayant d'antidater une attestation obtenue via :
https://media.interieur.gouv.fr/attestation-deplacement-derogatoire-covid-19/

On constate qu'il n'existe pas de validation dans le formulaire pour empêcher de déclarer une heure passée...
Par contre, le QRcode généré lui, mentionne bien l'heure déclarée, AINSI QUE, l'heure de la génération de l'attestation...
Ainsi, au moment du contrôle une bien mauvaise surprise vous attends... Pas cool.

Voici donc un serveur qui utilise la meme addresse que ci dessus mais qui va "corriger" le QRcode afin de couvrir vos fesses...


# instructions
Démarrez le serveur:
```
python attestaFion.py
```

Naviguez vers localhost:8080 (ou votre ip publique, dans ce cas mappez le port correspondant à la machine qui heberge le serveur), profitez de la liberté !