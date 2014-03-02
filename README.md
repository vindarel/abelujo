Abelujo - logiciel libre de gestion de petite librairie indépendante
-------


Projet actuellement en chantier. Il est néanmoins possible de:

- rechercher  des livres  par mots-clefs  ou par n°ISBN/EAN.  La recherche
  s'effectue sur le site chapitre.com.
- rechercher des CDs (via discogs.com)
- choisir combien d'exemplaires sont à ajouter dans le stock
- éditer les fiches de livres,
- chercher un titre  dans son stock et le marquer  comme vendu (ce qui
  décrémente de 1 son nombre d'exemplaires).

Nous  nous  basons sur  les  spécifications  fonctionnelles du  projet
Ruche:  http://ruche.eu.org/wiki  (auxquelles  nous  avons  d'ailleurs
participité). N'hésitez donc  pas à les lire et à nous  dire si ce que
nous faisons correspondra à vos besoins.

**Abelujo** signifie Ruche en Espéranto.


Installation
------------

Create a directory for the project:

    mkdir abelujo
    cd abelujo

Get the sources:

    git clone https://gitlab.com/vindarel/abelujo.git

Create  and activate  a virtual  environment (so  than we  can install
python  libraries locally,  not globally  to your  system). Do  as you
are used to, or do the following:

    sudo pip install virtualenvwrapper  # you need: sudo apt-get install python-pip
    source venv_create.sh

now  your  shell prompt  should  indicate  you  are in  the  "abelujo"
virtualenv. To quit  the virutal env, type "deactivate".  To enter it,
type "workon <TAB> abelujo".

To  install the  dependencies, create  and populate  the  database, run:

    ./install.sh


We are  done !  Now  to try Abelujo,  run the development  server like
this:

    python manage.py runserver
    # or set the port with:
    # python manage.py runserver 9876

and open  your browser  to [localhost:8000](http://127.0.0.1:8000).

Enjoy ! Don't forget to give feedback at ehvince (at) mailz.org !


Développement
-------------

Projet Django (2.5), en python (2.7).

Nous utilisons:

- des   templates   écrits  en   **jade**,   qui   compilent  en   html:
  http://jade-lang.com/ et pyjade
- **Grappelli**    pour   l'habillage    de    l'app   d'administration:
  http://grappelliproject.com/
- l'habillage CSS  classique de Bootstrap:  http://getbootstrap.com et
  django-bootstrap3

Pour récupérer les données sur  des sites distants, notre web scraping
se  fait avec  requests  et  beautifulsoup. Si  des
éléments de  la page  sont générés par  du JavaScript (par  exemple le
prix ou l'ean), alors nous utilisons selenium.

