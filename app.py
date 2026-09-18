from flask import Flask, redirect, render_template, request, flash
from werkzeug.security import generate_password_hash
import sqlite3
import config
import db

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")