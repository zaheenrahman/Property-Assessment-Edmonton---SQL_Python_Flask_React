from flask import Flask, jsonify
from models import db
from routes import *

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///edmontonproperties.db'
db.init_app(app)

# Define a simple route to test that the Flask app is working

init_app_routes(app)
@app.route('/')
def hello_world():
    return 'Hello, World!'

if __name__ == '__main__':
    app.run(debug=True)