Manuel d'utilisation
====================

Importer des notices depuis un fichier LibreOffice Calc (.ods)
--------------------------------------------------------------

Ceci n'est actuellement possible qu'à partir de la ligne de commande.

Votre tableau doit avoir au minimum les colonnes "titre" et
"éditeur". Ce sont les deux données qui servent à lancer une recherche
sur le web.

Usage::

    make odsimport src="yourfile.ods"
    # qui est un raccourci pour:
    # python manage.py runscript odsimport.py --script-args yourfile.ods

Le script va:
- lire le fichier ods et récupérer la liste des notices,
- pour chacune, lancer une recherche web (par défaut sur chapitre.com),
- vérifier la concordance des résultats de recherche avec vos données,
- répartir les résultats de recherche dans 3 groupes: les notices
  trouvées, celles trouvées mais sans ean, les non trouvées;
- demander confirmation si les deux groupes de données semblent
  différents,
- ajouter les notices et toutes leurs informations dans la base de
  données d'Abelujo.

Remarque: vous ne devez pas avoir le fichier ods ouvert en même temps.
