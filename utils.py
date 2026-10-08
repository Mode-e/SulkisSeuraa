
import datetime
import re
from flask import abort, flash, render_template, request, session
from SulkisSeuraa import time_slots


def check_csrf():
    if "csrf_token" not in request.form:
        abort(403)
    if request.form["csrf_token"] != session["csrf_token"]:
        abort(403)

def check_login():
    if "username" not in session:
        return render_template("not_registered.html")
    return None

def check_location(location):
    locations = ["Kluuvi Unisport", "Kumpula Unisport", "Meilahti Unisport",
                "Otaniemi Unisport", "Töölö Unisport", "Viikki Unisport"]
    if location not in locations:
        return f"Virhe, et voi varata vuorolle paikkaa {location}"
    return None

def check_time(time):
    proposed_day = request.form["date"]
    proposed_hours = request.form["hours"]
    proposed_minutes = request.form["minutes"]
    proposed_time = f"{proposed_day} {proposed_hours}:{proposed_minutes}"
    time = time_now()

    if proposed_time < time:
        return "Virhe: Et voi valita aikaa menneisyydestä"
    return None

def check_player_level(level_name):
    valid_levels = time_slots.get_levels()
    valid_names = [lvl["level_name"] for lvl in valid_levels]
    if level_name not in valid_names:
        return "Virhe: väärä pelaajan taso valittu"
    return True

def check_total_players(amount):
    valid_totals = time_slots.get_total()
    valid_amounts = [str(t["amount"]) for t in valid_totals]
    if str(amount) not in valid_amounts:
        return "Virhe: valitse määräksi kaksinpeli (2) tai nelinpeliksi (4)"
    return True

def check_players(players, user):
    for player in players:
        if user == player["username"]:
            return "Virhe: olet jo ilmoittautunut vuorolle"
    return None

def check_if_not_players(players, user):
    for player in players:
        if user == player["username"]:
            return None
    return "Virhe: Et ole ilmoittautunut vuoroon"

def check_description(description):
    if len(description) > 500:
        return "Virhe: Kuvaus saa olla enintään 500 merkkiä pitkä"
    return None

def check_availability(slot):
    if slot["player_count"] >= slot["total_players"]:
        return "Virhe: vuoro on täynnä"
    return None


def check_username(username):
    if len(username) < 3 or len(username) > 20:
        return "Virhe: käyttäjätunnuksen pituus pitää olla väliltä 3-20"
    if not re.match("^[a-zA-Z0-9_åäöÅÄÖ]+$", username):
        return "Virhe: käyttäjätunnuksessa saa olla vain kirjaimia, numeroita ja alaviivoja"
    return None

def check_password(password):
    if len(password) < 8 or len(password) > 20:
        return "Virhe: salasanan pituus pitää olla väliltä 8-20"
    return None

def check_slot(slot_id):
    slot = time_slots.get_slot(slot_id)
    if not slot:
        flash("VIRHE: Hakemaasi pelivuoroa ei ole olemassa.")
        return None
    return slot

def check_search(location, day, player_level, total_players, username):
    location = location if location else None
    day = day if day else None
    player_level = player_level if player_level else None
    total_players = total_players if total_players else None
    username = username if username else None

    return location, day, player_level, total_players, username

def check_prev():
    return request.referrer

def time_now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

def split_time(date_str):
    day, time = date_str.split(" ")
    hour, minutes = time.split(":")
    return day, hour, minutes

def create_error(slot, date, hour, minutes):
    return render_template("add_slot.html", slot=slot, date=date,
        hour=hour, minutes=minutes, locations=time_slots.get_locations(),
        levels=time_slots.get_levels(), total=time_slots.get_total()
    )

def edit_error(slot_data, date, hour, minutes):
    return render_template("edit_slot.html", slot=slot_data,
        slot_data=slot_data, date=date, hour=hour,
        minutes=minutes, locations=time_slots.get_locations(),
        levels=time_slots.get_levels(), total=time_slots.get_total()
    )

def get_profile_form():
    return {
        "player_level": request.form.get("player_level", ""),
        "description": request.form.get("description", "")
    }

def get_search_filters():
    return {
        "location": request.args.get("location_id", ""),
        "day": request.args.get("date", ""),
        "player_level": request.args.get("level_id", ""),
        "total_players": request.args.get("max_players_id", ""),
        "username": request.args.get("username", "")
    }

def get_create_slot_form():
    location_name = request.form.get("location_id")
    level_name = request.form.get("level_id")
    max_players_amount = request.form.get("max_players_id")
    location_id = time_slots.get_location_id(location_name)
    level_id = time_slots.get_level_id(level_name)
    max_players_id = time_slots.get_max_id(max_players_amount)

    slot = {
        "location": location_name,
        "location_id": location_id,
        "slot_time": f"{request.form.get('date')} {request.form.get('hours')}:{request.form.get('minutes')}",
        "player_level": level_name,
        "level_id": level_id,
        "total_players": max_players_amount,
        "max_players_id": max_players_id,
        "user_id": session.get("user_id")
    }
    return slot

def get_edit_slot_form():
    location_name = request.form.get("location_id")
    level_name = request.form.get("level_id")
    max_players_amount = request.form.get("max_players_id")
    location_id = time_slots.get_location_id(location_name)
    level_id = time_slots.get_level_id(level_name)
    max_players_id = time_slots.get_max_id(max_players_amount)

    slot = {
        "location": location_name,
        "location_id": location_id,
        "slot_time": f"{request.form.get('date')} {request.form.get('hours')}:{request.form.get('minutes')}",
        "player_level": level_name,
        "level_id": level_id,
        "total_players": max_players_amount,
        "max_players_id": max_players_id
    }
    return slot

def get_login_form():
    return {
        "username": request.form["username"],
        "password1": request.form["password1"]
    }

def get_registration_form():
    return {
        "username": request.form["username"],
        "password1": request.form["password1"],
        "password2": request.form["password2"]
    }
