# simply tests all the individual functions, especially those under application/routes/functions.py
import pytest
import os
from PIL import Image
from application.routes.functions import make_prediction, add_entry, edit_entry
from application.models import User

# test both the models on a few randomly selected images
# but first get all the directory of all the test images
image_dir = './tests/test_veg_images'
images = os.listdir(image_dir)
@pytest.mark.prediction
@pytest.mark.parametrize('image', images)
@pytest.mark.parametrize('model_input_size', [31, 128])
def test_prediction(image, model_input_size):
    img = Image.open(f'{image_dir}/{image}')                        # get the image into an Image object
    img_resized = img.resize((model_input_size, model_input_size))  # resize to the appropriate model's input size
    pred, _ = make_prediction(model_input_size, img_resized)        # make prediction
    assert pred.lower() == image.split('.')[0]                      # and test the prediction labels


# test the adding entry of user to see if adding the new user works, the email and password should have been the same after inserting
@pytest.mark.database
@pytest.mark.parametrize('email', ['wTf@mytest.com', 'A@b.C'])
@pytest.mark.parametrize('password', ['@#afaFAW#$4', 'jUsTg1v3m3DiSt!'])
def test_user_db(client, email, password):
    # create new user
    user = User(
        email = email,
        password = password
    )
    error = add_entry(user)    # attempt to add
    # check there is no error
    assert error is None

    # then check database and see if the new user is there
    user = User.query.filter_by(email=email).first()
    assert bool(user) and user.password == password


# now try add duplicated email
@pytest.mark.database
@pytest.mark.xfail(strict=True)
def test_xfail_user_db(client):
    user = User(
        email = 'test@test.com',
        password = 'Test12345$'
    )
    error = add_entry(user)
    # this should fail
    assert error is None

    # this should fail as well
    user = User.query.filter_by(email='test@test.com').first()
    assert bool(user) and user.password == 'Test12345$'


# test the editing of the user credential, this time with the authenticated client
@pytest.mark.database
@pytest.mark.parametrize('email', ['o@a.c', 'NOO@WHAT.cow'])
@pytest.mark.parametrize('password', ['Abc1234567!', '32qCF@QRTV$#T43t43VTQV4'])
def test_editing_user(authenticated_client, email, password):
    error = edit_entry(email=email, password=password)
    # first ensure there's no error
    assert error is None

    # then the email and password changed should be reflected
    user = User.query.filter_by(email=email).first()
    assert bool(user) and user.password == password