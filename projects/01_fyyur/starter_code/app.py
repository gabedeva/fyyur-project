#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from email.policy import default
import os
import dateutil.parser
import babel
import sys

from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify, abort, make_response
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import datetime
import itertools
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import exc, and_, Column, ForeignKey, Integer, Table
from sqlalchemy.orm import declarative_base, relationship
Base = declarative_base()
from models import db, Artist, Venue, Show

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)
# csrf = CSRFProtect(app)
# logger = logging.getLogger(__name__)

# TODO: connect to a local postgresql database
SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@localhost:5432/fyyur'

""" Filters """
def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Models - All models Imported from models at the top
#----------------------------------------------------------------------------#

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#   Controllers for Venues
#  ----------------------------------------------------------------

@app.route('/venues/create-venues', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create-venues', methods=['POST'])
def create_venue_submission():
    error = False
    try:
        venue = Venue()
        venue.name = request.form['name']
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.address = request.form['address']
        venue.phone = request.form['phone']
        tmp_genres = request.form.getlist('genres')
        venue.genres = ','.join(tmp_genres)
        venue.facebook_link = request.form['facebook_link']
        db.session.add(venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            flash('An error occured. Venue ' +
            request.form['name'] + ' Could not be listed!')
        else:
            flash('Venue ' + request.form['name'] +
            ' was successfully listed!')
    return render_template('pages/home.html')

# Controllers to get all venues
@app.route('/venues')
def venues():
    venues = Venue.query.order_by(Venue.state, Venue.city).all()

    previous_city = None
    previous_state = None
    data = []
    respdata = {}
    for venue in venues:
        venue_data = {
            'id': venue.id,
            'name': venue.name,
            'num_upcoming_shows': len(list(filter(lambda x: x.start_time > datetime.today(), venue.shows)))
        }
        if venue.city == previous_city and venue.state == previous_state:
            respdata['venues'].append(venue_data)
        else:
            if previous_city is not None:
                data.append(respdata)
            respdata['city'] = venue.city
            respdata['state'] = venue.state
            respdata['venues'] = [venue_data]
        previous_city = venue.city
        previous_state = venue.state

    data.append(respdata)
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_keyword = request.form.get('search_keyword')
    venues = Venue.query.filter(
        Venue.name.ilike('%{}%'.format(search_keyword))).all()

    data = []
    for venue in venues:
        searchres = {}
        searchres['id'] = venue.id
        searchres['name'] = venue.name
        searchres['num_upcoming_shows'] = len(venue.shows)
        data.append(searchres)

    dataresp = {}
    dataresp['count'] = len(data)
    dataresp['data'] = data

    return render_template('pages/search_venues.html', results=dataresp, search_keyword=request.form.get('search_keyword', ''))

# Get a venue by its id
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)

    past_shows = list(filter(lambda x: x.start_time <datetime.today(), venue.shows))
    upcoming_shows = list(filter(lambda x: x.start_time >= datetime.today(), venue.shows))

    past_shows = list(map(lambda x: x.show_artist(), past_shows))
    upcoming_shows = list(map(lambda x: x.show_artist(), upcoming_shows))

    data = venue.to_dict()
    data['past_shows'] = past_shows
    data['upcoming_shows'] = upcoming_shows
    data['past_shows_count'] = len(past_shows)
    data['upcoming_shows_count'] = len(upcoming_shows)

    return render_template('pages/show_venue.html', venue=data)

# edit a venue by its id
@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id).to_dict()
    return render_template('forms/edit_venue.html', form=form, venue=venue)

# edit a venue by its id
@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    venue = Venue.query.get(venue_id)

    error = False
    try:
        venue.name = request.form['name']
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.address = request.form['address']
        venue.phone = request.form['phone']
        tmp_genres = request.form.getlist('genres')
        venue.genres = ','.join(tmp_genres)  # convert list to string
        venue.facebook_link = request.form['facebook_link']
        db.session.add(venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            flash('An error occurred. Venue ' +
            request.form['name'] + ' could not be updated.')
        else:
            flash('Venue ' + request.form['name'] +
            ' was successfully updated!')

    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create-artists', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create-artists', methods=['POST'])
def create_artist_submission():
    form = ArtistForm()
    error = False
    try:
        artist = Artist()
        artist.name = request.form['name']
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.phone = request.form['phone']
        tmp_genres = request.form.getlist('genres')
        artist.genres = ','.join(tmp_genres)
        artist.website = request.form['website']
        artist.image_link = request.form['image_link']
        artist.facebook_link = request.form['facebook_link']
        artist.seeking_description = request.form['seeking_description']
        db.session.add(artist)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            flash('An error occurred. Artist ' +
            request.form['name'] + ' could not be listed.')
        else:
            flash('Artist ' + request.form['name'] +
            ' was successfully listed!')
        return render_template('pages/home.html')


# Controllers to get all artists
@app.route('/artists')
def artists():
    return render_template('pages/artists.html', artists = Artist.query.all())

# Get artists by id
@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # displaying the artist page with a given venue_id
    artist = Artist.query.get(artist_id)

    # This is an anonymous function for filtering past shows
    past_shows = list(filter(lambda x: x.start_time <datetime.today(), artist.shows)) 
    upcoming_shows = list(filter(lambda x: x.start_time >=
    datetime.today(), artist.shows))

    past_shows = list(map(lambda x: x.show_venue(), past_shows))
    # This is an anonymous function for filtering upcoming shows
    upcoming_shows = list(map(lambda x: x.show_venue(), upcoming_shows))

    data = artist.to_dict()
    print(data)
    data['past_shows'] = past_shows
    data['upcoming_shows'] = upcoming_shows
    data['past_shows_count'] = len(past_shows)
    data['upcoming_shows_count'] = len(upcoming_shows)
    return render_template('pages/show_artist.html', artist=data)

# Controller to Update an Artist
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    error = False
    try:
        artist = Artist.query.get(artist_id)
        artist.name = request.form['name']
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.phone = request.form['phone']
        tmp_genres = request.form.getlist('genres')
        artist.genres = ','.join(tmp_genres)
        artist.website = request.form['website']
        artist.image_link = request.form['image_link']
        artist.facebook_link = request.form['facebook_link']
        artist.seeking_description = request.form['seeking_description']
        db.session.add(artist)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            return redirect(url_for('server_error'))
        else:
            return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term')
    search_results = Artist.query.filter(
        Artist.name.ilike('%{}%'.format(search_term))).all()  # search results by ilike matching partern to match every search term

    response = {}
    response['count'] = len(search_results)
    response['data'] = search_results

    return render_template('pages/search_artists.html', results=response,
    search_term=request.form.get('search_term', ''))

#  Controllers for Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    shows = Show.query.all()
    data = []
    for show in shows:
        data.append({
            'venue_id': show.venue.id,
            'venue_name': show.venue.name,
            'artist_id': show.artist.id,
            'artist_name': show.artist.name,
            'artist_image_link': show.artist.image_link,
            'start_time': show.start_time.isoformat()
        })

    return render_template('pages/shows.html', shows=data)

# controller to create shows
@app.route('/shows/create-shows')
def create_shows():
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create-shows', methods=['POST'])
def create_show_submission():
    error = False
    try:
        show = Show()
        show.artist_id = request.form['artist_id']
        show.venue_id = request.form['venue_id']
        show.start_time = request.form['start_time']
        db.session.add(show)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            flash('An error occurred. Requested show could not be listed.')
        else:
            flash('Requested show was successfully listed')
        return render_template('pages/home.html')

# renders 404 page
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

# if there's an internal server error
@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# set Default port:
if __name__ == '__main__':
    app.run()

# Or specify the port manually:

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

