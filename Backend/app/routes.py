from flask import Flask, jsonify, request
from models import db, Property, ResidentialProperty, CommercialProperty, Neighborhood, Ward

app = Flask(__name__)
def init_app_routes(app):
    @app.route('/api/properties/neighborhood/<neighborhood_name>', methods=['GET'])
    def get_properties_by_neighborhood(neighborhood_name):
            properties = Property.query.join(Neighborhood).filter(Neighborhood.name == neighborhood_name).all()
            return jsonify([property.to_dict() for property in properties])
    @app.route('/api/properties', methods=['GET'])
    def get_properties():
        properties = Property.query.all()
        return jsonify([property.to_dict() for property in properties])

    @app.route('/api/properties/<int:property_id>', methods=['GET'])
    def get_property_details(property_id):
        prop = Property.query.get(property_id)
        if prop:
            prop_dict = prop.to_dict()
            # Assume `to_dict()` only includes generic Property information
            # We now extend it with specific details based on the type
            if hasattr(prop, 'residential_info') and prop.residential_info:
                prop_dict.update({'assessed_value': prop.residential_info.assessed_value})
            elif hasattr(prop, 'commercial_info') and prop.commercial_info:
                prop_dict.update({
                    'assessed_value': prop.commercial_info.assessed_value,
                    'business_type': prop.commercial_info.business_type
                })
            return jsonify(prop_dict)
        return jsonify({"error": "Property not found"}), 404

    @app.route('/api/properties/valued_above/<int:value>', methods=['GET'])
    def get_properties_valued_above(value):
        # Query for Residential Properties valued above the given value
        residential_properties = ResidentialProperty.query.filter(ResidentialProperty.assessed_value > value).all()
        
        # Query for Commercial Properties valued above the given value
        commercial_properties = CommercialProperty.query.filter(CommercialProperty.assessed_value > value).all()

        # Combine results, assuming you have to_dict methods on ResidentialProperty and CommercialProperty
        properties = [prop.to_dict() for prop in residential_properties] + [prop.to_dict() for prop in commercial_properties]
        
        # Optionally, sort the combined results by assessed value if needed
        properties.sort(key=lambda x: x['assessed_value'], reverse=True)
        
        return jsonify(properties)

    @app.route('/api/properties/type/<property_type>', methods=['GET'])
    def get_properties_by_type(property_type):
        if property_type.lower() == 'commercial':
            properties = CommercialProperty.query.all()
        elif property_type.lower() == 'residential':
            properties = ResidentialProperty.query.all()
        else:
            return jsonify({"error": "Invalid property type"}), 400
        return jsonify([property.to_dict() for property in properties])

    @app.route('/api/neighborhoods/stats', methods=['GET'])
    def get_neighborhood_stats():
        # Query for average assessed value of residential properties by neighborhood
        res_stats = db.session.query(
            Neighborhood.name,
            db.func.avg(ResidentialProperty.assessed_value).label('average_residential_value')
        ).join(Property, Property.id == ResidentialProperty.property_id)\
        .join(Neighborhood, Neighborhood.id == Property.neighborhood_id)\
        .group_by(Neighborhood.name).all()

        # Query for average assessed value of commercial properties by neighborhood
        com_stats = db.session.query(
            Neighborhood.name,
            db.func.avg(CommercialProperty.assessed_value).label('average_commercial_value')
        ).join(Property, Property.id == CommercialProperty.property_id)\
        .join(Neighborhood, Neighborhood.id == Property.neighborhood_id)\
        .group_by(Neighborhood.name).all()

        # Combine the stats into a single dictionary {neighborhood: {res_avg, com_avg}}
        combined_stats = {}
        for name, avg_val in res_stats:
            combined_stats[name] = {'average_residential_value': avg_val}
        
        for name, avg_val in com_stats:
            if name in combined_stats:
                combined_stats[name]['average_commercial_value'] = avg_val
            else:
                combined_stats[name] = {'average_commercial_value': avg_val}

        # Convert the combined_stats dictionary to a list of dictionaries for jsonify
        result = [{'neighborhood': name, **vals} for name, vals in combined_stats.items()]
        return jsonify(result)
    
    @app.route('/api/neighborhoods/total_values', methods=['GET'])
    def get_neighborhood_total_values():
        # Aggregate total residential property values by neighborhood
        res_totals = db.session.query(
            Neighborhood.name,
            db.func.sum(ResidentialProperty.assessed_value).label('total_residential_value')
        ).join(Property, Property.id == ResidentialProperty.property_id)\
        .join(Neighborhood, Neighborhood.id == Property.neighborhood_id)\
        .group_by(Neighborhood.name).all()

        # Aggregate total commercial property values by neighborhood
        com_totals = db.session.query(
            Neighborhood.name,
            db.func.sum(CommercialProperty.assessed_value).label('total_commercial_value')
        ).join(Property, Property.id == CommercialProperty.property_id)\
        .join(Neighborhood, Neighborhood.id == Property.neighborhood_id)\
        .group_by(Neighborhood.name).all()

        # Initialize a dictionary to hold the combined stats
        combined_totals = {}

        # Populate the dictionary with residential totals
        for name, total_val in res_totals:
            if name not in combined_totals:
                combined_totals[name] = {'total_residential_value': total_val or 0, 'total_commercial_value': 0}
            else:
                combined_totals[name]['total_residential_value'] = total_val or 0

        # Update the dictionary with commercial totals
        for name, total_val in com_totals:
            if name not in combined_totals:
                combined_totals[name] = {'total_residential_value': 0, 'total_commercial_value': total_val or 0}
            else:
                combined_totals[name]['total_commercial_value'] = total_val or 0

        # Prepare the response data
        result = [{
            'neighborhood': name,
            'total_residential_value': values['total_residential_value'],
            'total_commercial_value': values['total_commercial_value']
        } for name, values in combined_totals.items()]

        return jsonify(result)
    
    @app.route('/api/neighborhoods/max_total_values', methods=['GET'])
    def get_neighborhoods_max_total_values():
        # Use the aggregation logic from the previous route
        combined_totals = aggregate_neighborhood_totals()

        # Sort the combined totals by the sum of residential and commercial values, descending
        sorted_totals = sorted(combined_totals.items(), key=lambda x: x[1]['total_residential_value'] + x[1]['total_commercial_value'], reverse=True)

        # Prepare and return the sorted list
        result = format_sorted_totals(sorted_totals)
        return jsonify(result)
        
    @app.route('/api/neighborhoods/min_total_values', methods=['GET'])
    def get_neighborhoods_min_total_values():
        # Use the aggregation logic from the previous route
        combined_totals = aggregate_neighborhood_totals()

        # Sort the combined totals by the sum of residential and commercial values, ascending
        sorted_totals = sorted(combined_totals.items(), key=lambda x: x[1]['total_residential_value'] + x[1]['total_commercial_value'])

        # Prepare and return the sorted list
        result = format_sorted_totals(sorted_totals)
        return jsonify(result)
        
def format_sorted_totals(sorted_totals):
    # Transform the sorted list of tuples into the desired format
    result = [{
        'neighborhood': name,
        'total_value': values['total_residential_value'] + values['total_commercial_value'],
        'total_residential_value': values['total_residential_value'],
        'total_commercial_value': values['total_commercial_value']
    } for name, values in sorted_totals]
    return result

def aggregate_neighborhood_totals():
    # Aggregate total residential property values by neighborhood
    res_totals = db.session.query(
        Neighborhood.name,
        db.func.sum(ResidentialProperty.assessed_value).label('total_residential_value')
    ).join(Property, Property.id == ResidentialProperty.property_id)\
     .join(Neighborhood, Neighborhood.id == Property.neighborhood_id)\
     .group_by(Neighborhood.name).all()

    # Aggregate total commercial property values by neighborhood
    com_totals = db.session.query(
        Neighborhood.name,
        db.func.sum(CommercialProperty.assessed_value).label('total_commercial_value')
    ).join(Property, Property.id == CommercialProperty.property_id)\
     .join(Neighborhood, Neighborhood.id == Property.neighborhood_id)\
     .group_by(Neighborhood.name).all()

    # Initialize a dictionary to hold the combined stats
    combined_totals = {}

    # Populate the dictionary with residential totals
    for name, total_val in res_totals:
        if name not in combined_totals:
            combined_totals[name] = {'total_residential_value': total_val or 0, 'total_commercial_value': 0}
        else:
            combined_totals[name]['total_residential_value'] = total_val or 0

    # Update the dictionary with commercial totals
    for name, total_val in com_totals:
        if name not in combined_totals:
            combined_totals[name] = {'total_residential_value': 0, 'total_commercial_value': total_val or 0}
        else:
            combined_totals[name]['total_commercial_value'] = total_val or 0

    return combined_totals

if __name__ == '__main__':
    app.run(debug=True)