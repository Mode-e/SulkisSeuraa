import math
import secrets

import time_slots
import users
import utils
from config import secret_key
from flask import Flask, abort, flash, redirect, render_template, request, session
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.secret_key = secret_key


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


@app.errorhandler(403)
def forbidden(error):
    return render_template("403.html"), 403


@app.route("/edit_message/<int:message_id>/<int:slot_id>", methods=["GET", "POST"])
def edit_message(message_id, slot_id):
    if access_denied := utils.check_login():
        return access_denied
    message = time_slots.get_edit_message(message_id)
    if not message:
        abort(404)
    if message["sender_username"] != session["username"]:
        abort(403)

    if request.method == "POST":
        utils.check_csrf()
        if "delete" in request.form:
            time_slots.delete_message(message_id)
            flash("Viesti poistettu onnistuneesti.", "success")
            return redirect(f"/signup/{slot_id}")

        message_text = request.form.get("message_text")
        if message_text and message_text.strip():
            if len(message_text.strip()) > 129:
                flash("Viesti on liian pitkä (enintään 129 merkkiä)", "error")
            else:
                time_slots.update_message(message_id, message_text.strip())
                return redirect(f"/signup/{slot_id}")
        else:
            flash("Viesti ei voi olla tyhjä", "error")
    return render_template("edit_message.html", message=message, slot_id=slot_id)


@app.route("/signup/<int:slot_id>", methods=["GET", "POST"])
def signup_page(slot_id):
    if access_denied := utils.check_login():
        return access_denied
    if not users.is_profile_ready(session["user_id"]):
        flash("Päivitä profiilisi tiedot ennen vuorotoimintojen käyttöä!", "error")
        return redirect(f"/edit_info/{session['user_id']}")

    prev = utils.check_prev()

    slot = utils.check_slot(slot_id)
    if not slot:
        return redirect(prev)

    if slot["slot_time"] < utils.time_now():
        flash("Virhe: tietoja menneistä vuoroista ei ole saatavilla", "error")
        return redirect(prev)

    players = time_slots.get_players(slot_id)

    signed_up = False
    for player in players:
        if player["username"] == session["username"]:
            signed_up = True

    if request.method == "POST":
        message_text = request.form.get("message_text")
        if message_text and message_text.strip() and signed_up:
            if len(message_text.strip()) > 129:
                flash("Viesti on liian pitkä (enintään 129 merkkiä)", "error")
            else:
                time_slots.add_message(
                    slot_id, session["username"], message_text.strip()
                )
        thread_count = time_slots.get_message_count(slot_id)
        last_page = math.ceil(thread_count / 10)
        last_page = max(last_page, 1)

        return redirect(f"/signup/{slot_id}?page={last_page}")
    page = request.args.get("page", 1, type=int)
    page_size = 6
    thread_count = time_slots.get_message_count(slot_id)
    page_count = math.ceil(thread_count / page_size)
    page_count = max(page_count, 1)
    page = max(1, min(page, page_count))

    # Haetaan vain tämän sivun 10 viestiä
    messages = time_slots.get_messages_paged(slot_id, page, page_size)
    return render_template(
        "signup.html",
        slot=slot,
        players=players,
        signed_up=signed_up,
        prev=prev,
        messages=messages,
        page=page,
        page_count=page_count,
    )


@app.route("/cancel_signup/<int:slot_id>", methods=["POST"])
def cancel_signup(slot_id):
    if access_denied := utils.check_login():
        return access_denied
    utils.check_csrf()

    prev = utils.check_prev()
    slot = utils.check_slot(slot_id)
    if not slot:
        return redirect(prev)

    if slot["slot_time"] < utils.time_now():
        flash("Virhe: et voi perua ilmoitusta menneeseen vuoroon", "error")
        return redirect(prev)

    not_signed_up = utils.check_if_not_players(
        time_slots.get_players(slot_id), session["username"]
    )
    if isinstance(not_signed_up, str):
        flash(not_signed_up, "error")
        return redirect(prev)

    time_slots.cancel_signup(session["user_id"], slot_id)
    return redirect("/my_slots")


@app.route("/apply/<int:slot_id>", methods=["POST"])
def signup(slot_id):
    if access_denied := utils.check_login():
        return access_denied
    utils.check_csrf()
    if not users.is_profile_ready(session["user_id"]):
        flash("Päivitä profiilisi tiedot ennen vuorotoimintojen käyttöä!", "error")
        return redirect(f"/edit_info/{session['user_id']}")

    prev = utils.check_prev()
    slot = utils.check_slot(slot_id)
    if not slot:
        return redirect(prev)

    if slot["slot_time"] < utils.time_now():
        flash("Virhe: et voi ilmoittautua menneeseen vuoroon", "error")
        return redirect(prev)

    errors = []

    if isinstance(available := utils.check_availability(slot), str):
        errors.append(available)

    if isinstance(
        signed_up := utils.check_players(
            time_slots.get_players(slot_id), session["username"]
        ),
        str,
    ):
        errors.append(signed_up)

    if errors:
        for error in errors:
            flash(error, "error")
        return redirect(prev)

    time_slots.signup(session["user_id"], slot_id)
    return redirect("/my_slots")


@app.route("/search", methods=["GET"])
def search():
    if access_denied := utils.check_login():
        return access_denied

    search_data = utils.get_search_filters()
    (location, day, player_level, total_players, username) = utils.check_search(
        search_data["location"],
        search_data["day"],
        search_data["player_level"],
        search_data["total_players"],
        search_data["username"],
    )

    page = request.args.get("page", 1, type=int)
    page_size = 10
    time_now = utils.time_now()

    # Lasketaan kuinka monta vuoroa haku löytää yhteensä
    thread_count = time_slots.count_found_slots(
        time_now, location, day, player_level, total_players, username
    )
    page_count = math.ceil(thread_count / page_size)
    page_count = max(page_count, 1)

    page = max(1, min(page, page_count))

    # 2. HAETAAN VAIN TÄMÄN SIVUN HAKUTULOKSET
    results = time_slots.find_slots_paged(
        time_now, location, day, player_level, total_players, username, page, page_size
    )

    return render_template(
        "search.html",
        results=results,
        location=location,
        day=day,
        player_level=player_level,
        total_players=total_players,
        username=username,
        locations=time_slots.get_locations(),
        levels=time_slots.get_levels(),
        total=time_slots.get_total(),
        page=page,
        page_count=page_count,
    )


@app.route("/edit_slot/<int:slot_id>", methods=["GET", "POST"])
def edit_slot(slot_id):
    if access_denied := utils.check_login():
        return access_denied

    prev = utils.check_prev()
    slot = time_slots.get_slot(slot_id)
    day_now = utils.time_now().split(" ")
    if not slot:
        abort(404)

    if session["user_id"] != slot["user_id"]:
        abort(403)

    if request.method == "POST":
        utils.check_csrf()
        players = time_slots.get_players(slot_id)
        if request.form.get("action") == "delete":
            if len(players) > 1:
                users.update_modified_slots_count(session["user_id"])
            time_slots.delete_slot(slot_id)
            flash("Pelivuoro poistettu.")
            return redirect("/my_slots")
        data = utils.get_edit_slot_form()
        d, h, m = utils.split_time(data["slot_time"])
        errors = []

        if isinstance(time_error := utils.check_time(data["slot_time"]), str):
            errors.append(time_error)

        if isinstance(location_error := utils.check_location(data["location"]), str):
            errors.append(location_error)

        if isinstance(
            player_level_error := utils.check_player_level(data["player_level"]), str
        ):
            errors.append(player_level_error)

        if isinstance(
            total_players_error := utils.check_total_players(data["total_players"]), str
        ):
            errors.append(total_players_error)

        if errors:
            for error in errors:
                flash(error, "error")
            return utils.edit_error(data, d, h, m)

        time_slots.update_slot(
            slot_id,
            data["location_id"],
            data["slot_time"],
            data["level_id"],
            data["max_players_id"],
        )
        if len(players) > 1:
            users.update_modified_slots_count(session["user_id"])
        flash("Pelivuoro päivitetty onnistuneesti.", "success")
        return redirect("/my_slots")

    date, hour, minutes = utils.split_time(slot["slot_time"])

    return render_template(
        "edit_slot.html",
        slot=slot,
        slot_data=slot,
        date=date,
        hour=hour,
        minutes=minutes,
        prev=prev,
        time=day_now[0],
        locations=time_slots.get_locations(),
        levels=time_slots.get_levels(),
        total=time_slots.get_total(),
    )


@app.route("/my_info/<int:user_id>")
def my_info(user_id):
    if access_denied := utils.check_login():
        return access_denied

    info = users.user_info(user_id)
    if not info:
        abort(404)
    page = request.args.get("page", 1, type=int)
    page_size = 8
    time_now = utils.time_now()

    thread_count = time_slots.get_created_slots_count(time_now, user_id)
    page_count = math.ceil(thread_count / page_size)
    page_count = max(page_count, 1)

    # Korjataan sivunumero lennosta sallittuihin rajoihin ilman redirectiä
    page = max(1, min(page, page_count))

    # Haetaan tämän sivun vuorot
    upcoming = time_slots.get_created_slots_paged(time_now, user_id, page, page_size)

    created = time_slots.all_created_slots(user_id)
    future = time_slots.my_slots(user_id, utils.time_now())
    past = time_slots.past_slots(user_id, utils.time_now())

    return render_template(
        "my_info.html",
        upcoming=upcoming,
        info=info,
        my_page=user_id == session["user_id"],
        created=created,
        future=future,
        past=past,
        page=page,
        page_count=page_count,
        current_user_id=session.get("user_id"),
    )


@app.route("/edit_info/<int:user_id>", methods=["GET", "POST"])
def edit_info(user_id):
    if access_denied := utils.check_login():
        return access_denied

    prev = utils.check_prev()

    if request.method == "POST":
        utils.check_csrf()
        if user_id != session["user_id"]:
            abort(403)

        data = utils.get_profile_form()
        errors = []
        level_error = utils.check_player_level(data["player_level"])
        if isinstance(
            level_error := utils.check_player_level(data["player_level"]), str
        ):
            errors.append(level_error)

        if isinstance(
            description_error := utils.check_description(data["description"]), str
        ):
            errors.append(description_error)

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("edit_info.html", info=data, prev=prev)

        users.user_update(data, user_id)

        return redirect(f"/my_info/{user_id}")

    info = users.user_info(user_id)[0]
    print("INFON SISÄLTÖ:", info)
    return render_template("edit_info.html", info=info, prev=prev)


@app.route("/my_slots")
def my_slots():
    if access_denied := utils.check_login():
        return access_denied
    page = request.args.get("page", 1, type=int)
    page_size = 8
    user_id = session["user_id"]
    thread_count = time_slots.get_my_upcoming_count(utils.time_now(), user_id)
    page_count = math.ceil(thread_count / page_size)
    page_count = max(page_count, 1)
    page = max(1, min(page, page_count))

    upcoming = time_slots.get_my_upcoming_paged(
        utils.time_now(), user_id, page, page_size
    )

    return render_template(
        "my_slots.html", upcoming=upcoming, page=page, page_count=page_count
    )


@app.route("/")
@app.route("/<int:page>")
def index(page=1):
    page = request.args.get("page", 1, type=int)
    page_size = 8

    if "user_id" in session:
        # Kirjautuneelle lasketaan vain ne tulevat vuorot, joille hän EI OLE ilmoittautunut
        thread_count = time_slots.get_upcoming_slots_count(
            utils.time_now(), user_id=session["user_id"]
        )
    else:
        # Kirjautumattomalle lasketaan kaikki tulevat vuorot
        thread_count = time_slots.get_upcoming_slots_count(utils.time_now())

    page_count = math.ceil(thread_count / page_size)
    page_count = max(page_count, 1)

    if page < 1:
        return redirect("/?page=1")
    if page > page_count:
        return redirect("/?page=" + str(page_count))

    if "user_id" in session:
        my_open_slots = time_slots.get_my_upcoming_paged(
            utils.time_now(), session["user_id"], page, page_size
        )
        open_slots = time_slots.get_upcoming_slots_paged(
            utils.time_now(), page, page_size, user_id=session["user_id"]
        )
    else:
        my_open_slots = []
        open_slots = time_slots.get_upcoming_slots_paged(
            utils.time_now(), page, page_size
        )

    return render_template(
        "index.html",
        my_open_slots=my_open_slots,
        open_slots=open_slots,
        page=page,
        page_count=page_count,
    )


@app.route("/add_slot", methods=["GET"])
def add_slot():
    if access_denied := utils.check_login():
        return access_denied
    if not users.is_profile_ready(session["user_id"]):
        flash("Päivitä profiilisi tiedot ennen vuorotoimintojen käyttöä!", "error")
        return redirect(f"/edit_info/{session['user_id']}")

    locations = time_slots.get_locations()
    levels = time_slots.get_levels()
    total = time_slots.get_total()
    return render_template(
        "add_slot.html",
        date=utils.time_now(),
        locations=locations,
        levels=levels,
        total=total,
    )


@app.route("/create_slot", methods=["POST"])
def create_slot():
    if access_denied := utils.check_login():
        return access_denied
    utils.check_csrf()
    slot = utils.get_create_slot_form()
    date, hour, minutes = utils.split_time(slot["slot_time"])
    errors = []

    if isinstance(location_error := utils.check_location(slot["location"]), str):
        errors.append(location_error)

    if isinstance(time_error := utils.check_time(slot["slot_time"]), str):
        errors.append(time_error)

    if isinstance(
        player_level_error := utils.check_player_level(slot["player_level"]), str
    ):
        errors.append(player_level_error)

    if isinstance(
        total_players_error := utils.check_total_players(slot["total_players"]), str
    ):
        errors.append(total_players_error)

    if errors:
        for error in errors:
            flash(error, "error")
        return utils.create_error(slot, date, hour, minutes)
    slot_id = time_slots.create_slot(slot)
    time_slots.signup(session["user_id"], slot_id)
    return redirect("/")


@app.route("/logout")
def logout():
    del session["username"]
    del session["user_id"]
    return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    user = utils.get_login_form()
    if not users.user_exists(user["username"]):
        flash("VIRHE: käyttäjätunnus väärin", "error")
        return render_template("login.html", user=user)

    user_id = users.user_login(user["username"], user["password1"])

    if user_id:
        session["username"] = user["username"]
        session["user_id"] = user_id
        session["csrf_token"] = secrets.token_hex(16)
        return redirect("/")

    flash("VIRHE: väärä salasana", "error")
    return render_template("login.html", user=user)


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/create", methods=["POST"])
def create():
    user = utils.get_registration_form()
    username_error = utils.check_username(user["username"])
    errors = []
    if isinstance(username_error, str):
        errors.append(username_error)

    password_error = utils.check_password(user["password1"])
    if isinstance(password_error, str):
        errors.append(password_error)

    if users.user_exists(user["username"]):
        errors.append("VIRHE: käyttäjätunnus varattu")

    if user["password1"] != user["password2"]:
        errors.append("VIRHE: väärä salasana")

    if errors:
        for error in errors:
            flash(error, "error")
        return render_template("register.html", user=user)

    password_hash = generate_password_hash(user["password1"])
    users.user_create(user["username"], password_hash)
    flash("Käyttäjätunnus luotu", "success")
    return redirect("/login")
