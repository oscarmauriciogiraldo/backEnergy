from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import io
import base64

matplotlib.use("agg")

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return 'Hello World'

@app.route('/api/energy')
def get_energy():
    return{
        'energy': [
            {'id': 1, 'name':'solar'}, 
            {'id': 2, 'name':'eolica'}, 
            {'id': 3, 'name':'hidroelectrica'}, 
            {'id': 4, 'name':'geotermica'}, 
            
        ]
    }


if __name__ == '__main__':
    app.run(debug = True)