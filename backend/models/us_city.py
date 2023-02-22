from config.db import db

class UsCity(db.Model):
    __tablename__ = 'us_cities'

    id = db.Column(db.Integer, primary_key = True)
    city = db.Column(db.String(50), nullable=False)
    city_ascii = db.Column(db.String(50), nullable=False)
    state_id = db.Column(db.String(50), nullable=False)
    state_name = db.Column(db.String(50), nullable=False)
    county_fips = db.Column(db.String(50), nullable=False)
    county_name = db.Column(db.String(50), nullable=False)
    lat = db.Column(db.String(50), nullable=False)
    lng = db.Column(db.String(50), nullable=False)
    population = db.Column(db.String(50), nullable=False)
    density = db.Column(db.String(50), nullable=False)
    source = db.Column(db.String(50), nullable=False)
    military = db.Column(db.String(50), nullable=False)
    incorporated = db.Column(db.String(50), nullable=False)
    timezone = db.Column(db.String(50), nullable=False)
    ranking = db.Column(db.String(50), nullable=False)
    zips = db.Column(db.Text(), nullable=False)

    def as_dict(self):
        response = dict()
        response['id'] = self.id
        return response