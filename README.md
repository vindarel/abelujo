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

Nous nous basons sur les spécifications fonctionnelles du projet
Ruche, auxquelles nous avons participé:
http://ruche.eu.org/wiki/Specifications_fonctionnelles. Nous avons
écrit ce que nous avons compris de la gestion des dépôts, des
commandes, etc. N'hésitez donc pas à les lire et à nous dire si ce que
nous commençons correspondra à vos besoins.

**Abelujo** signifie Ruche en Espéranto.


Installation
------------

Get the sources:

    git clone https://gitlab.com/vindarel/abelujo.git

it creates the directory "abelujo":

   cd abelujo

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

Enjoy ! Don't forget to give feedback at ehvince at mailz dot org !

### How to update ###


For now, when you update the sources (git pull), you certainly will
have to run the installation process again. We may have updated some
python packages and the database is very likely to change too (and we
didn't set up some DB schema migration yet, meaning you'll loose your
data).


Développement
-------------

Projet Django (1.6), en python (2.7).

Nous utilisons:

- des   templates   écrits  en   **jade**,   qui   compilent  en   html:
  http://jade-lang.com/ et pyjade
- **Grappelli**    pour   l'habillage    de    l'app   d'administration:
  http://grappelliproject.com/
- l'habillage CSS  classique de Bootstrap:  http://getbootstrap.com et
  django-bootstrap3

Pour récupérer les données sur des sites distants, notre web scraping
se fait avec requests, selenium (quand une page est générée par du
javascript) et beautifulsoup, et nous louchons fortement vers
[scrapy](http://doc.scrapy.org/en/latest/intro/overview.html).
