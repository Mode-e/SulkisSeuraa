# 🏸 Sulkapallosovellus (tikawe-sovellus)

## Sovelluksen toiminnot ##
+ Sovelluksessa käyttäjät pystyvät etsimään peliseuraa sulkapalloon. Ilmoituksessa lukee missä ja milloin pelivuoro on sekä tarvittava pelaajien määrä.

+ Käyttäjä pystyy luomaan tunnuksen ja kirjautumaan sisään sovellukseen.

+ Käyttäjä pystyy lisäämään ilmoituksia, muokkaamaan ja poistamaan niitä.

+ Käyttäjä näkee sovellukseen lisätyt ilmoitukset.

+ Käyttäjä pystyy etsimään ilmoituksia sen perusteella, milloin vuoro on.

+ Käyttäjäsivu näyttää, montako ilmoitusta käyttäjä on lähettänyt ja listan ilmoituksista.

+ Käyttäjä pystyy valitsemaan esimerkiksi seuraavia luokitteluja:
    + Pelipaikka: Kumpula Unisport tai Otaniemi Unisport
    + Pelaajan taso: aloittelija, harrastaja, kilpataso

+ Käyttäjä pystyy ilmoittautumaan pelivuoroon. Ilmoittautuessa näkee ketkä käyttäjät ovat ilmoittautuneet.

## Sovelluksen käyttöönotto ##

+ $ python3.10 -m venv venv
+ $ source venv/bin/activate
+ $ pip install flask
+ $ python seed.py
+ $ flask run