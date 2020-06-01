#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
import sys
#import datetime
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form, CsrfProtect
from forms import *
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.config['SECRET_KEY'] = "it's a secret"
csrf = CsrfProtect()
# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(2048))
    seeking_talent = db.Column(db.Boolean(), default=False)
    seeking_description = db.Column(db.String())
    venue_genres = db.relationship('VenueGenres', backref = 'Venue')
    shows = db.relationship('Shows', backref = 'Venue')

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(2048))
    seeking_venue = db.Column(db.Boolean(), default=False)
    seeking_description = db.Column(db.String())
    artist_genres = db.relationship('ArtistGenres', backref = 'Artist')
    shows = db.relationship('Shows', backref = 'Artist')

class Shows(db.Model):
    __tablename__ = 'Show'
    start_time = db.Column(db.DateTime, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), primary_key=True)

class ArtistGenres(db.Model):
    __tablename__ = 'artistgenres'
    id = db.Column(db.Integer, primary_key=True) 
    genre = db.Column(db.String(20))
    artist = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)

class VenueGenres(db.Model):
    __tablename__ = 'venuegenres'
    id = db.Column(db.Integer, primary_key=True)
    genre = db.Column(db.String(20))
    venue = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # data=[{
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "venues": [{
  #     "id": 1,
  #     "name": "The Musical Hop",
  #     "num_upcoming_shows": 0,
  #   }, {
  #     "id": 3,
  #     "name": "Park Square Live Music & Coffee",
  #     "num_upcoming_shows": 1,
  #   }]
  # }, {
  #   "city": "New York",
  #   "state": "NY",
  #   "venues": [{
  #     "id": 2,
  #     "name": "The Dueling Pianos Bar",
  #     "num_upcoming_shows": 0,
  #   }]
  # }]
  data = []
  locations = db.session.query(Venue.state, Venue.city).distinct().all()
  now = datetime.now()
  for location in locations:
    allVenues = db.session.query(Venue.id, Venue.name).filter(Venue.city==location.city, Venue.state==location.state)
    print(allVenues)
    singleData = {"city": location.city, "state": location.state}
    listOfVenues = []
    for venue in allVenues:
      numOfupshows = db.session.query(func.count(Shows.venue_id)).filter(Shows.venue_id==venue.id, Shows.start_time > now).scalar()
      currentVenue = {"id": venue.id, "name": venue.name, "num_upcoming_shows": numOfupshows}
      listOfVenues.append(currentVenue)
    singleData["venues"] = listOfVenues
    data.append(singleData)
    
  print(data)
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search = request.form['search_term']
  records = db.session.query(Venue.id, Venue.name).filter(Venue.name.ilike("%" + search + "%"))
  data = []
  now = datetime.now()
  for record in records:
    num_upcoming_shows = db.session.query(func.count(Shows.venue_id)).filter(Shows.venue_id==record.id, Shows.start_time > now).scalar()
    venue = {
      "id": record.id,
      "name": record.name,
      "num_upcoming_shows": num_upcoming_shows,
    }
    data.append(venue)
  response = {
    "count": len(data),
    "data": data
  }
  # response={
  #   "count": 1,
  #   "data": [{
  #     "id": 2,
  #     "name": "The Dueling Pianos Bar",
  #     "num_upcoming_shows": 0,
  #   }]
  # }
  return render_template('pages/search_venues.html', results=response, search_term=search)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  now = datetime.now()
  venue = db.session.query(Venue).filter(Venue.id==venue_id).first()
  genreQuery = db.session.query(VenueGenres.genre).filter(VenueGenres.venue==venue_id)
  pastQuery = db.session.query(Shows.start_time, Shows.artist_id).filter(Shows.venue_id==venue_id, Shows.start_time < now)
  upcoQuery = db.session.query(Shows.start_time, Shows.artist_id).filter(Shows.venue_id==venue_id, Shows.start_time > now)
  past_shows_count = db.session.query(func.count(Shows.venue_id)).filter(Shows.venue_id==venue_id, Shows.start_time < now).scalar()
  upcoming_shows_count = db.session.query(func.count(Shows.venue_id)).filter(Shows.venue_id==venue_id, Shows.start_time > now).scalar()
  past_shows = []
  genres = []
  for query in genreQuery:
    genres.append(query.genre)
  for query in pastQuery:
    artist = db.session.query(Artist.name, Artist.image_link).filter(Artist.id==query.artist_id).first()
    time = query.start_time
    start_time = time.isoformat()
    currentArtist = {
      "artist_id": query.artist_id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
       "start_time": start_time
    }
    past_shows.append(currentArtist)
  upcoming_shows = []
  for query in upcoQuery:
    artist = db.session.query(Artist.name, Artist.image_link).filter(Artist.id==query.artist_id).first()
    time = query.start_time
    start_time = time.isoformat()
    currentArtist = {
      "artist_id": query.artist_id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": start_time
    }
    upcoming_shows.append(currentArtist)
  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": past_shows_count,
    "upcoming_shows_count": upcoming_shows_count
  }
  # data1={
  #   "id": 1,
  #   "name": "The Musical Hop",
  #   "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
  #   "address": "1015 Folsom Street",
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "phone": "123-123-1234",
  #   "website": "https://www.themusicalhop.com",
  #   "facebook_link": "https://www.facebook.com/TheMusicalHop",
  #   "seeking_talent": True,
  #   "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
  #   "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
  #   "past_shows": [{
  #     "artist_id": 4,
  #     "artist_name": "Guns N Petals",
  #     "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
  #     "start_time": "2019-05-21T21:30:00.000Z"
  #   }],
  #   "upcoming_shows": [],
  #   "past_shows_count": 1,
  #   "upcoming_shows_count": 0,
  # }
  # data2={
  #   "id": 2,
  #   "name": "The Dueling Pianos Bar",
  #   "genres": ["Classical", "R&B", "Hip-Hop"],
  #   "address": "335 Delancey Street",
  #   "city": "New York",
  #   "state": "NY",
  #   "phone": "914-003-1132",
  #   "website": "https://www.theduelingpianos.com",
  #   "facebook_link": "https://www.facebook.com/theduelingpianos",
  #   "seeking_talent": False,
  #   "image_link": "https://images.unsplash.com/photo-1497032205916-ac775f0649ae?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=750&q=80",
  #   "past_shows": [],
  #   "upcoming_shows": [],
  #   "past_shows_count": 0,
  #   "upcoming_shows_count": 0,
  # }
  # data3={
  #   "id": 3,
  #   "name": "Park Square Live Music & Coffee",
  #   "genres": ["Rock n Roll", "Jazz", "Classical", "Folk"],
  #   "address": "34 Whiskey Moore Ave",
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "phone": "415-000-1234",
  #   "website": "https://www.parksquarelivemusicandcoffee.com",
  #   "facebook_link": "https://www.facebook.com/ParkSquareLiveMusicAndCoffee",
  #   "seeking_talent": False,
  #   "image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
  #   "past_shows": [{
  #     "artist_id": 5,
  #     "artist_name": "Matt Quevedo",
  #     "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
  #     "start_time": "2019-06-15T23:00:00.000Z"
  #   }],
  #   "upcoming_shows": [{
  #     "artist_id": 6,
  #     "artist_name": "The Wild Sax Band",
  #     "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #     "start_time": "2035-04-01T20:00:00.000Z"
  #   }, {
  #     "artist_id": 6,
  #     "artist_name": "The Wild Sax Band",
  #     "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #     "start_time": "2035-04-08T20:00:00.000Z"
  #   }, {
  #     "artist_id": 6,
  #     "artist_name": "The Wild Sax Band",
  #     "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #     "start_time": "2035-04-15T20:00:00.000Z"
  #   }],
  #   "past_shows_count": 1,
  #   "upcoming_shows_count": 1,
  # }
  # data = list(filter(lambda d: d['id'] == venue_id, [data1, data2, data3]))[0]
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False
  form =  VenueForm(request.form)
  if form.validate():
    try:
       venue = Venue()
       form.populate_obj(venue)
       db.session.add(venue)
       db.session.commit()
       id = venue.id
       for genre in form.genres.data:
         gen = VenueGenres(genre=genre, venue=id)
         db.session.add(gen)
       db.session.commit()
    except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
    finally:
      db.session.close()
    if error:
      flash('An error occurred. Venue ' + form.name + ' could not be listed.')
      return redirect(url_for('create_venue_form'))
    else:
      flash('Venue ' + form.name.data + ' was successfully listed!')
  else:
    print(form.errors)
    flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
    return redirect(url_for('create_venue_form'))
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['POST'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  venue = db.session.query(Venue).filter(Venue.id==venue_id).first()
  try:
    db.session.query(Shows).filter(Shows.venue_id==venue.id).delete()
    db.session.query(VenueGenres).filter(VenueGenres.venue==venue_id).delete()
    db.session.delete(venue)
    db.session.commit()
  except:
    flash("Unable to delte Venue")
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  flash("Venue as been successfully deleted")
  return redirect(url_for('index'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = []
  artists = db.session.query(Artist.id, Artist.name)
  for artist in artists:
    currentArtist = {"id": artist.id, "name": artist.name}
    data.append(currentArtist)
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search = request.form['search_term']
  records = db.session.query(Artist.id, Artist.name).filter(Artist.name.ilike("%" + search + "%"))
  data = []
  now = datetime.now()
  for record in records:
    num_upcoming_shows = db.session.query(func.count(Shows.artist_id)).filter(Shows.artist_id==record.id, Shows.start_time > now).scalar()
    artist = {
      "id": record.id,
      "name": record.name,
      "num_upcoming_shows": num_upcoming_shows,
    }
    data.append(artist)
  response = {
    "count": len(data),
    "data": data
  }
  print(response)
  # response={
  #   "count": 1,
  #   "data": [{
  #     "id": 4,
  #     "name": "Guns N Petals",
  #     "num_upcoming_shows": 0,
  #   }]
  # }
  return render_template('pages/search_artists.html', results=response, search_term=search)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  now = datetime.now()
  artist = db.session.query(Artist).filter(Artist.id==artist_id).first()
  genreQuery = db.session.query(ArtistGenres.genre).filter(ArtistGenres.artist==artist_id)
  pastQuery = db.session.query(Shows.start_time, Shows.venue_id).filter(Shows.artist_id==artist_id, Shows.start_time < now)
  upcoQuery = db.session.query(Shows.start_time, Shows.venue_id).filter(Shows.artist_id==artist_id, Shows.start_time > now)
  past_shows_count = db.session.query(func.count(Shows.artist_id)).filter(Shows.artist_id==artist_id, Shows.start_time < now).scalar()
  upcoming_shows_count = db.session.query(func.count(Shows.artist_id)).filter(Shows.artist_id==artist_id, Shows.start_time > now).scalar()
  past_shows = []
  genres = []
  for query in genreQuery:
    genres.append(query.genre)
  for query in pastQuery:
    venue = db.session.query(Venue.name, Venue.image_link).filter(Venue.id==query.venue_id).first()
    time = query.start_time
    start_time = time.isoformat()
    currentVenue = {
      "venue_id": query.venue_id,
      "venue_name": venue.name,
      "venue_image_link": venue.image_link,
       "start_time": start_time
    }
    past_shows.append(currentVenue)
  upcoming_shows = []
  for query in upcoQuery:
    venue = db.session.query(Venue.name, Venue.image_link).filter(Venue.id==query.venue_id).first()
    time = query.start_time
    start_time = time.isoformat()
    currentVenue = {
      "venue_id": query.venue_id,
      "venue_name": venue.name,
      "venue_image_link": venue.image_link,
       "start_time": start_time
    }
    upcoming_shows.append(currentVenue)
  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": past_shows_count,
    "upcoming_shows_count": upcoming_shows_count
  }
  # data1={
  #   "id": 4,
  #   "name": "Guns N Petals",
  #   "genres": ["Rock n Roll"],
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "phone": "326-123-5000",
  #   "website": "https://www.gunsnpetalsband.com",
  #   "facebook_link": "https://www.facebook.com/GunsNPetals",
  #   "seeking_venue": True,
  #   "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
  #   "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
  #   "past_shows": [{
  #     "venue_id": 1,
  #     "venue_name": "The Musical Hop",
  #     "venue_image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
  #     "start_time": "2019-05-21T21:30:00.000Z"
  #   }],
  #   "upcoming_shows": [],
  #   "past_shows_count": 1,
  #   "upcoming_shows_count": 0,
  # }
  # data2={
  #   "id": 5,
  #   "name": "Matt Quevedo",
  #   "genres": ["Jazz"],
  #   "city": "New York",
  #   "state": "NY",
  #   "phone": "300-400-5000",
  #   "facebook_link": "https://www.facebook.com/mattquevedo923251523",
  #   "seeking_venue": False,
  #   "image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
  #   "past_shows": [{
  #     "venue_id": 3,
  #     "venue_name": "Park Square Live Music & Coffee",
  #     "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
  #     "start_time": "2019-06-15T23:00:00.000Z"
  #   }],
  #   "upcoming_shows": [],
  #   "past_shows_count": 1,
  #   "upcoming_shows_count": 0,
  # }
  # data3={
  #   "id": 6,
  #   "name": "The Wild Sax Band",
  #   "genres": ["Jazz", "Classical"],
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "phone": "432-325-5432",
  #   "seeking_venue": False,
  #   "image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #   "past_shows": [],
  #   "upcoming_shows": [{
  #     "venue_id": 3,
  #     "venue_name": "Park Square Live Music & Coffee",
  #     "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
  #     "start_time": "2035-04-01T20:00:00.000Z"
  #   }, {
  #     "venue_id": 3,
  #     "venue_name": "Park Square Live Music & Coffee",
  #     "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
  #     "start_time": "2035-04-08T20:00:00.000Z"
  #   }, {
  #     "venue_id": 3,
  #     "venue_name": "Park Square Live Music & Coffee",
  #     "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
  #     "start_time": "2035-04-15T20:00:00.000Z"
  #   }],
  #   "past_shows_count": 0,
  #   "upcoming_shows_count": 3,
  # }
  # data = list(filter(lambda d: d['id'] == artist_id, [data1, data2, data3]))[0]
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  
  record = db.session.query(Artist).filter(Artist.id==artist_id).first()
  genreQuery = db.session.query(ArtistGenres.genre).filter(ArtistGenres.artist==artist_id)
  genres = []
  for query in genreQuery:
    genres.append(query.genre)
  artist={
    "id": artist_id,
    "name": record.name,
    "genres": genres,
    "city": record.city,
    "state": record.state,
    "phone": record.phone,
    "website": record.website,
    "facebook_link": record.facebook_link,
    "seeking_venue": record.seeking_venue,
    "seeking_description": record.seeking_description,
    "image_link": record.image_link
  }
  form = ArtistForm()
  #form.name.data = artist.name
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  form = ArtistForm(request.form)
  error = False
  if form.validate:
    try:
      artist = db.session.query(Artist).filter(Artist.id==artist_id).first()
      form.populate_obj(artist)
      db.session.commit()
    except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
    finally:
      db.session.close()
    if error:
      flash('An error occurred. Artist ' + form.name.data + ' could not be updated.')
      return redirect(url_for('edit_artist', artist_id=artist_id)) 
  else:
    flash('Artist ' + form.name.data + ' was successfully updated!')
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  record = db.session.query(Venue).filter(Venue.id==venue_id).first()
  genreQuery = db.session.query(VenueGenres.genre).filter(VenueGenres.venue==venue_id)
  genres = []
  for query in genreQuery:
    genres.append(query.genre)
  venue={
    "id": record.id,
    "name": record.name,
    "genres": genres,
    "address": record.address,
    "city": record.city,
    "state": record.state,
    "phone": record.phone,
    "website": record.website,
    "facebook_link": record.facebook_link,
    "seeking_talent": record.seeking_talent,
    "seeking_description": record.seeking_description,
    "image_link": record.image_link
  }
  form = VenueForm(obj=venue)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  form = VenueForm(request.form)
  error = False
  if form.validate():
    try:
      venue = db.session.query(Venue).filter(Venue.id==venue_id).first()
      form.populate_obj(venue)
      db.session.commit()
    except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
    finally:
      db.session.close()
    if error:
      flash('An error occurred. Venue ' + form.name.data + ' could not be updated.')
      return redirect(url_for('edit_venue', venue_id=venue_id))
  else:
    flash('Venue ' + form.name.data + ' was successfully updated!')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error = False
  form = ArtistForm(request.form)
  if form.validate():
    try:
      artist = Artist()
      form.populate_obj(artist)
      db.session.add(artist)
      db.session.commit()
      id = artist.id
      for genre in form.genres.data:
        gen = ArtistGenres(genre=genre, artist=id)
        db.session.add(gen)
      db.session.commit()
    except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
    finally:
      db.session.close()
    if error:
      flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
      return redirect(url_for('create_artist_form'))
    else:
      flash('Artist ' + form.name.data + ' was successfully listed!')
  else:
    print(form.errors)
    return redirect(url_for('create_artist_form'))
  return render_template('pages/home.html') 

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  data = []
  records = db.session.query(Venue.id.label("venue_id"), Venue.name.label("venue_name"), Artist.id.label("artist_id"), Artist.name.label("artist_name"), Artist.image_link.label("artist_image_link"), Shows.start_time).join(Artist, Artist.id==Shows.artist_id).join(Venue, Venue.id==Shows.venue_id)
  print(records)
  for record in records:
    time = record.start_time
    start_time = time.isoformat()
    showData = {
      "venue_id": record.venue_id,
      "venue_name": record.venue_name,
      "artist_id": record.artist_id,
      "artist_name": record.artist_name,
      "artist_image_link": record.artist_image_link,
      "start_time": start_time
    }
    data.append(showData)
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create', methods=['GET'])
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  form = ShowForm(request.form)
  if form.validate():
    try:
      show = Shows(start_time=form.start_time.data, artist_id=form.artist_id.data, venue_id=form.venue_id.data)
      db.session.add(show)
      db.session.commit()
    except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
    finally:
      db.session.close()
    if error:
      flash('An error occurred. Show  could not be listed.')
      return redirect(url_for('/shows/create'))
    else:
      flash('Show  was successfully listed!')
  else:
    print(form.errors)
    return redirect(url_for('/shows/create'))
  return render_template('pages/home.html')  

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
