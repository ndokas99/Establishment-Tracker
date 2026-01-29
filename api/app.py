from flask import Flask, render_template, render_template_string, request, make_response, jsonify, session, redirect, \
    url_for, flash
from sqlalchemy import text
from flask_apscheduler import APScheduler

from folium import Map, Icon, Marker, Circle
from overpy import Overpass
import overpy.exception

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

        session['lat1'], session['lon1'], session['dist'], session['est_type'] = request.get_json().values()
        return make_response(jsonify({}))

    else:
        session['sid'] = str(uuid4())
        return url_for('track')


@lru_cache
def create_markers(cache, distance, lat, lon):
    try:
        results = Overpass(retry_timeout=900).query(f"""
            [timeout:900][maxsize:1073741824];
            node(around: {distance * 1000}, {lat}, {lon})
            ["amenity"~"{session['est_type']}"]
            ["name"];
            out body;
        """)
    except overpy.exception.OverpassGatewayTimeout:
        flash("The server timed out, try to rerun your request.")
        return redirect('/')

    details = []
    for node in results.nodes:
        nodeLat = float(node.lat)
        nodeLon = float(node.lon)
        detail = {
            "id": f"{node.id}",
            "lat": nodeLat,
            "lon": nodeLon,
            "name": node.tags["name"],
            "type": node.tags["amenity"],
            "distance": calc_dist(nodeLat, nodeLon)
        }

        ids = [["street", "addr:street"], ["opening hours", "opening_hours"], ["internet access", "internet_access"],
               ["phone", "phone"], ["email", "email"]]

        for key, val in ids:
            try:
                detail[key] = node.tags[val]
            except KeyError:
                continue
        details.append(detail)

    return sorted(details, key=lambda k: k['distance'])


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

    details = create_markers(session['est_type'], dist, lat1, lon1)
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
        return render_template("tracker.html", details=details, establishment=est_map[session['est_type']])
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
