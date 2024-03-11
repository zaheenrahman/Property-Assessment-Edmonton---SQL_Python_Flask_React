from flask_sqlalchemy import SQLAlchemy
from flask import jsonify

db = SQLAlchemy()

class Property(db.Model):
    __tablename__ = 'properties'
    id = db.Column(db.Integer, primary_key=True)
    house_number = db.Column(db.String(50))
    street_name = db.Column(db.String(100))
    garage = db.Column(db.String(1))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    neighborhood_id = db.Column(db.Integer, db.ForeignKey('neighborhoods.id'))
    ward_id = db.Column(db.Integer, db.ForeignKey('wards.id'))

    def to_dict(self):
        return {
            'id': self.id,
            'house_number': self.house_number,
            'street_name': self.street_name,
            'garage': self.garage,
            'latitude': self.latitude,
            'longitude': self.longitude,
        }

    # Relationships
    residential_info = db.relationship('ResidentialProperty', backref='property', uselist=False)
    commercial_info = db.relationship('CommercialProperty', backref='property', uselist=False)

    def to_detailed_dict(self):
        """Converts this Property object into a dict, including detailed information."""
        data = self.to_dict()  
        data['neighborhood'] = self.neighborhood.name if self.neighborhood else None
        data['ward'] = self.ward.name if self.ward else None
        return data
    
class ResidentialProperty(db.Model):
    __tablename__ = 'residential_properties'
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'))
    assessed_value = db.Column(db.Float)

    def to_dict(self):
        return {
            'id': self.id,
            'property_id': self.property_id,
            'assessed_value': self.assessed_value
        }

class CommercialProperty(db.Model):
    __tablename__ = 'commercial_properties'
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'))
    assessed_value = db.Column(db.Float)
    business_type = db.Column(db.String(100))

    def to_dict(self):
        return {
            'id': self.id,
            'property_id': self.property_id,
            'assessed_value': self.assessed_value,
            'business_type': self.business_type
        }

class Neighborhood(db.Model):
    __tablename__ = 'neighborhoods'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    properties = db.relationship('Property', backref='neighborhood')

class Ward(db.Model):
    __tablename__ = 'wards'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    properties = db.relationship('Property', backref='ward')