# functions for performing something so to make the views.py less cluttered
import json
import requests
import numpy as np
from ..models import User
from flask_login import current_user
from .. import db

# vegetable labels
LABELS = ['Bean',
            'Bitter_Gourd',
            'Bottle_Gourd',
            'Brinjal',
            'Broccoli',
            'Cabbage',
            'Capsicum',
            'Carrot',
            'Cauliflower',
            'Cucumber',
            'Papaya',
            'Potato',
            'Pumpkin',
            'Radish',
            'Tomato']

# function to transform image data, resizing has been done earlier
def transformer(img, pixels):
    pixelScaler = np.vectorize(lambda x: x / 255)   # to normalise the image data

    # simply convert to grayscale and then into numpy array
    img = pixelScaler(np.array(img.convert('L')))

    # reshape and return
    return img.reshape(1, pixels, pixels, 1)

# function to make a prediction
def make_prediction(model_input_size, img):

    # first transform the image
    img = transformer(img, model_input_size)  

    # note that I can literally select the model just by inserting the the model input size into the url
    url = f'https://twob01-2239745-shawnlim-ca2-models.onrender.com/v1/models/model_{model_input_size}:predict'

    # then set up the stuff for posting prediction
    data = json.dumps({
        'signature_name' : 'serving_default',
        'instances' : img.tolist()
    })
    header = {'content_type' : 'application/json'}

    # post the request and get the response
    res = requests.post(url, data, headers=header)
    pred = json.loads(res.text)['predictions']
    return LABELS[np.argmax(pred)], pred    # return the prediction label as well as the list of probabilities for each label, to be later store for advanced search

# function to add new user or history into the database
def add_entry(entry) -> Exception | None:
    try:
        db.session.add(entry)
        db.session.commit()
        return None
    except Exception as error:
        db.session.rollback()
        return error
    
# function to edit email or password of the user
def edit_entry(email = None, password = None) -> Exception | None:
    try:
        user = User.query.get(current_user.id)
        if email:
            user.email = email
        if password:
            user.password = password
        db.session.commit()
    except Exception as error:
        db.session.rollback()
        return error