from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os

API_KEY = os.environ.get("API")
IMG_URL = "https://image.tmdb.org/t/p/w1280"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)
db = SQLAlchemy()
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies.db"
db.init_app(app)


class RateForm(FlaskForm):
    rating = StringField(label="Your rating out of 10 e.g. 7.5", validators=[DataRequired()])
    review = StringField(label="Your Review", validators=[DataRequired()])
    submit_button = SubmitField(label="Done")


class AddForm(FlaskForm):
    title = StringField(label="Movie Title", validators=[DataRequired()])
    add_button = SubmitField(label="Add Movie")


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=["POST", "GET"])
def edit():
    movie_form = RateForm()
    movie_id = request.args.get("id")
    movie_selected = db.session.execute(db.select(Movie).where(Movie.id == movie_id)).scalar()
    if movie_form.validate_on_submit():
        movie_selected.rating = float(movie_form.rating.data)
        movie_selected.review = movie_form.review.data
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html", form=movie_form, movie=movie_selected)


@app.route("/delete")
def delete():
    movie_id = request.args.get("id")
    movie_to_delete = db.session.get(Movie, movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/add", methods=["POST", "GET"])
def add():
    movie_form = AddForm()
    if movie_form.validate_on_submit():
        movie_title = movie_form.title.data
        response = requests.get(url="https://api.themoviedb.org/3/search/movie", params={"api_key": API_KEY,
                                                                                         "query": movie_title})
        data = response.json()["results"]
        return render_template("select.html", choices=data)
    return render_template("add.html", form=movie_form)


@app.route("/find")
def find_movie():
    movie_id = request.args.get("id")
    if movie_id:
        response = requests.get(url=f"https://api.themoviedb.org/3/movie/{movie_id}", params={"api_key": API_KEY,
                                                                                              "movie_id": movie_id})
        data = response.json()
        new_movie = Movie(title=data["title"], year=data["release_date"].split("-")[0], description=data["overview"],
                          img_url=f"{IMG_URL}{data['poster_path']}")
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("edit", id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
