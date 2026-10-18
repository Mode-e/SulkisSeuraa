# 🏸 Sulkapallosovellus (tikawe-sovellus)

## Sovelluksen toiminnot ##
+ Sovelluksessa käyttäjät pystyvät etsimään peliseuraa sulkapalloon. Ilmoituksessa lukee missä ja milloin pelivuoro on sekä tarvittava pelaajien määrä.

+ Käyttäjä pystyy luomaan tunnuksen ja kirjautumaan sisään sovellukseen.

+ Käyttäjä pystyy lisäämään ilmoituksia, muokkaamaan ja poistamaan niitä.

+ Käyttäjä näkee sovellukseen lisätyt ilmoitukset.

+ Käyttäjä pystyy etsimään ilmoituksia sen perusteella, milloin vuoro on.

+ Käyttäjäsivu näyttää, montako ilmoitusta käyttäjä on lähettänyt ja listan ilmoituksista.

+ Käyttäjä pystyy valitsemaan esimerkiksi seuraavia luokitteluja:
    + **Pelipaikka:** Kumpula Unisport tai Otaniemi Unisport
    + **Pelaajan taso:** aloittelija, harrastaja, kilpataso

+ Käyttäjä pystyy ilmoittautumaan pelivuoroon. Ilmoittautuessa näkee ketkä käyttäjät ovat ilmoittautuneet.


## Raportti: Toiminta suurella tietomäärällä

Sovellusta testattu suurilla tietomäärillä käyttämällä *seed.py* -skriptiä.
+ **Käyttäjät:** 1 000 kappaletta
+ **Pelivuorot (time_slots):** 10 000 kappaletta
+ **Viestit (messages):** 1 000 000 kappaletta

### Suorituskyky ja optimointi
Ilman optimointia pelivuorokohtaisten viestien haku hidastui oli erittäin hidasta, koska miljoona viestiriviä käydään muuten läpi joka kerta kun sivu ladataan.

Suorituskykyä parannettu lisäämällä tietokantaindeksit. Listaus vaikutuksista:
+ Nopeampi vuorojen haku ja järjestäminen ajan mukaan
+ Nopeampi haku pelipaikan mukaan
+ Nopeampi haku pelivuoron tason mukaan
+ Nopeampi haku tietyn vuoron viesteille
+ Ilmoittautuminen pelivuorolle nopeampaa


## Sovelluksen käyttöönotto ##

+ $ python3.10 -m venv venv
+ $ source venv/bin/activate
+ $ pip install flask
+ $ python seed.py
+ $ flask run