from flask import Flask, render_template, render_template_string, request, make_response, jsonify, session, redirect, \
    url_for, flash
from sqlalchemy import text
from flask_apscheduler import APScheduler

from folium import Map, Icon, Marker, Circle
from overpy import Overpass, Result
from overpy.exception import OverpassGatewayTimeout, OverpassUnknownContentType

from math import cos
from datetime import datetime, timezone
from functools import lru_cache
from uuid import uuid4
from os import path, getenv

from api.models import db, Session, create_database
from api.utils import calc_dist, est_map


BASE_DIR = path.dirname(path.dirname(path.abspath(__file__)))

app = Flask(__name__,
            template_folder=path.join(BASE_DIR, "templates"),
            static_folder=path.join(BASE_DIR, "static"))

app.debug = False

app.config.update({
    "SECRET_KEY": 'H475GGH58H4DG374H9GY48THT85',
    "SQLALCHEMY_DATABASE_URI": getenv('DATABASE_SQLALCHEMY_URL') or "sqlite:///database.db",
    "SQLALCHEMY_TRACK_MODIFICATIONS": False,
})

db.init_app(app)

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()


@app.route('/')
def index():
    return render_template("index.html", establishments=est_map.items())


@app.route('/unsupported')
def unavailable():
    return render_template_string("<h1>Geolocation feature does not work on this platform</h1>")


@app.route('/track', methods=['POST'])
def track():
    if session.get('sid'):
        if Session.query.filter_by(sessionId=session['sid']).first():
            pass
        else:
            user = Session(sessionId=session['sid'], sessionTime=datetime.now(timezone.utc))
            db.session.add(user)
            db.session.commit()

        session["rand"] = 0
        session['lat1'], session['lon1'], session['dist'], session['est_values'] = request.get_json().values()
        return make_response(jsonify({}))

    else:
        session['sid'] = str(uuid4())
        return url_for('track')


@lru_cache
def create_markers(est_values, distance, lat, lon, cache_check):
    lazy = False
    key = est_map[est_values][1][:-1]
    sign = est_map[est_values][1][-1]
    try:
        way_values = ["hotel|motel|resort|lodge|cabin|museum", "worship", "parking", ""]
        results = Overpass(retry_timeout=900).query(f"""
            [out:json][timeout:900][maxsize:1073741824];
            {"way" if est_values in way_values else "node"}(around: {distance * 1000}, {lat}, {lon})
            ["{key}"{sign}"{est_values}"]
            ["name"];
            out tags center;
        """)
    except (OverpassUnknownContentType, OverpassGatewayTimeout):
        results = Result()
        lazy = True
        with app.app_context():
            session['rand'] += 1
        # flash("The server timed out, try to rerun your request.")
        # return redirect('/')

    details = []

    # todo: add functionality to combine nodes and ways if both are populated

    for item in (results.nodes if results.nodes else results.ways):
        itemLat = float(item.lat if results.nodes else item.center_lat)
        itemLon = float(item.lon if results.nodes else item.center_lon)
        detail = {
            "id": f"{item.id}",
            "lat": itemLat,
            "lon": itemLon,
            "coordinates": f"{(itemLat, itemLon)}",
            "name": item.tags["name"],
            "type": key,
            "distance": calc_dist(itemLat, itemLon)
        }

        ids = [
            ["street", "addr:street"],
            ["opening hours", "opening_hours"],
            ["internet access", "internet_access"],
            ["phone", "phone"],
            ["email", "email"],
            ["wheelchair access", "wheelchair"],
            ["cash payment", "payment:cash"],
            ['card payment', "payment:credit_cards"]
        ]

        for prop, val in ids:
            if item.tags.get(val):
                detail[prop] = item.tags[val]
        details.append(detail)

    return sorted(details, key=lambda k: k['distance']), lazy


@app.route('/showMap')
def show_map():
    try:
        lat1, lon1, dist = session['lat1'], session['lon1'], session['dist']
    except KeyError:
        return redirect("/")

    latDiff = (360 / 40075) * dist
    lonDiff = (360 / (cos(lat1) * 40075))
    bounds = [[lat1 - latDiff, lon1 - lonDiff], [lat1 + latDiff, lon1 + lonDiff]]

    mainMap = Map(location=[lat1, lon1], min_lat=bounds[0][0], min_lon=bounds[0][1], max_lat=bounds[1][0], max_lon=bounds[1][1], zoom_start=15)
    Marker(location=[lat1, lon1], tooltip="You are here", icon=Icon(color="red", icon="user")).add_to(mainMap)
    Circle(location=(lat1, lon1), radius=dist * 1000).add_to(mainMap)

    details, lazy = create_markers(session['est_values'], dist, lat1, lon1, session['rand'])
    if not isinstance(details, list):
        flash("The server had an error, try to rerun your request.")
        return redirect('/')

    for detail in details:
        Marker(
            location=[detail["lat"], detail["lon"]], tooltip=f"{detail['name']}", icon=Icon(color="blue", icon="building", prefix="fa")
        ).add_to(mainMap)

    user = Session.query.filter_by(sessionId=session['sid']).first()
    if user:
        user.sessionMap = mainMap.get_root().render()
        db.session.commit()
        return render_template("tracker.html", details=details, establishment=est_map[session['est_values']][0], lazy=lazy)
    else:
        return redirect('/')


@app.route('/map')
def embed_map():
    user = Session.query.filter_by(sessionId=session['sid']).first()
    if user:
        return render_template_string(user.sessionMap)
    else:
        return redirect('/', 500)


@scheduler.task("interval", id="DbCLeaner", seconds=300)
def clear_old_session():
    with app.app_context():
        for data in Session.query.all():
            seconds = (datetime.now() - data.sessionTime).seconds
            if seconds > 300:
                Session.query.filter_by(sessionId=data.sessionId).delete()
                db.session.commit()
        #with db.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        #    conn.execute(text("VACUUM ANALYZE"))


if __name__ == '__main__':
    with app.app_context():
        create_database()
        app.run("0.0.0.0")
