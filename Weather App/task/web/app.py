import datetime
import sys

import requests
from flask import Flask
from flask import render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
import re


def add_city_to_db(name):
    global db
    city = City(name=name)
    db.session.add(city)
    db.session.commit()


def get_cities():
    global db
    try:
        cities = db.session.query(City).all()
    except:
        return None
    return cities


def get_day_state(timezone):
    local_time = (datetime.datetime.utcnow() + datetime.timedelta(seconds=timezone)).strftime("%H")

    day_state = None

    if 6 <= int(local_time) <= 16:
        day_state = 'day'
    elif 17 <= int(local_time) <= 23:
        day_state = 'evening-morning'
    elif 0 <= int(local_time) <= 5:
        day_state = 'night'
    return day_state


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
app.secret_key = "super secret key"
db = SQLAlchemy(app)


class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

    def __repr__(self):
        return '<City %r>' % self.name


db.create_all()

api_key = '8cd377e1a0b8969ec95284d348cab23a'
weather_dict = {}


@app.route('/')
def index():
    cities = get_cities()

    if cities is None:
        return render_template('index.html')

    for city in cities:

        r = requests.get(f'https://api.openweathermap.org/data/2.5/weather?q={city.name}&units=metric&appid={api_key}')
        data = r.json()

        temp_celcius = round(data['main']['temp'])
        weather = data['weather'][0]['main']
        day_state = get_day_state(data['timezone'])
        weather_dict.update({city.name: [temp_celcius, weather, day_state, city.id]})

    return render_template('index.html', weather=weather_dict)


@app.route('/add', methods=['POST', 'GET'])
def add_city():
    name = request.form['city_name'].upper().strip()
    response = requests.get(f'https://api.openweathermap.org/data/2.5/weather?q={name}&units=metric&appid={api_key}')
    if not response:
        flash("The city doesn't exist!")
        return redirect('/')
    added = City.query.filter_by(name=name).first()
    if added:
        flash("The city has already been added to the list!")
    else:
        add_city_to_db(name)
    return redirect('/')


@app.route('/delete/<city_id>', methods=['POST', 'GET'])
def delete(city_id):
    city_id = re.sub("[^0-9]", "", city_id)
    city = db.session.query(City).filter_by(id=city_id).first()
    db.session.delete(city)
    db.session.commit()
    weather_dict.pop(city.name)
    return redirect('/')


# don't change the following way to run flask:
if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()
