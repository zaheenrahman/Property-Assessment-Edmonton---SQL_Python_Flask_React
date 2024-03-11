import csv
from models import db, Property, ResidentialProperty, CommercialProperty, Neighborhood, Ward
from flask import current_app

def init_db(app):
    with app.app_context():
        db.create_all()  # Creates the tables based on your models

def import_data_from_csv(csv_filepath):
    with current_app.app_context():
        with open(csv_filepath, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            # Batch process tracker
            process_count = 0
            for row in reader:
                # Check and add neighborhood
                neighborhood_name = row['Neighbourhood']
                neighborhood = Neighborhood.query.filter_by(name=neighborhood_name).first()
                if not neighborhood:
                    neighborhood = Neighborhood(name=neighborhood_name)
                    db.session.add(neighborhood)
                    # Committing immediately to ensure foreign key constraints are met
                    db.session.commit()

                # Check and add ward
                ward_name = row['Ward']
                ward = Ward.query.filter_by(name=ward_name).first()
                if not ward:
                    ward = Ward(name=ward_name)
                    db.session.add(ward)
                    db.session.commit()

                # Add property details
                new_property = Property(
                    house_number=row.get('House Number', None),
                    street_name=row['Street Name'],
                    garage=row['Garage'] == 'Y',
                    latitude=float(row['Latitude']),
                    longitude=float(row['Longitude']),
                    neighborhood_id=neighborhood.id,
                    ward_id=ward.id
                )
                db.session.add(new_property)

                # Handle different property types
                if row['Assessment Class 1'] == 'RESIDENTIAL':
                    res_property = ResidentialProperty(
                        property=new_property,
                        assessed_value=float(row['Assessed Value'])
                    )
                    db.session.add(res_property)
                elif row['Assessment Class 1'] == 'COMMERCIAL':
                    com_property = CommercialProperty(
                        property=new_property,
                        assessed_value=float(row['Assessed Value']),
                        business_type=row.get('Business Type', 'Not Specified')
                    )
                    db.session.add(com_property)
                
                process_count += 1
                # Batch commit; adjust the batch size as needed
                if process_count % 100 == 0:
                    db.session.commit()
                    print(f"Processed {process_count} records.")

            # Commit any remaining records
            db.session.commit()
            print(f"Finished processing. Total records processed: {process_count}.")