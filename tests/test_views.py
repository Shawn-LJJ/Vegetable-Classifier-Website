# test to see if I can get all the web pages
import pytest
import os
from PIL import Image
import io
import numpy as np
from application.models import User, History
from application.routes.functions import LABELS
from bs4 import BeautifulSoup

# easily make the soup
def make_soup(res) -> BeautifulSoup:
    return BeautifulSoup(res, 'html.parser')

# test to see if I can retrieve the basic sites
@pytest.mark.parametrize('url', ['/', '/index', '/home', '/signup', '/signin'])
@pytest.mark.website    # group this as testing web service being able to GET web page
def test_page(client, url):
    res = client.get(url)
    assert res.status_code == 200

# same thing but with authenticated client to see if I can retrieve more sites
@pytest.mark.parametrize('url', ['/', '/index', '/home', '/signup', '/signin', '/setting', '/search'])
@pytest.mark.website    # group this as testing web service being able to GET web page
def test_page(authenticated_client, url):
    res = authenticated_client.get(url)
    assert res.status_code == 200


# now I expect these urls to not be ever implemented, so expect this to fail
@pytest.mark.parametrize('url', ['/ligmaballz', '/givemedistinction'])
@pytest.mark.website    # group this as testing web service fail to GET web page that does not exist
@pytest.mark.xfail(strict=True)
def test_nonexistent_page(client, url):
    res = client.get(url)
    assert res.status_code == 200


# test to see if can post a prediction and predict it correctly
image_dir = './tests/test_veg_images'
images = os.listdir(image_dir)
@pytest.mark.parametrize('image', images)
@pytest.mark.parametrize('model_input_size', ['128 pixels model', '31 pixels model'])
@pytest.mark.api        # group this as testing the API functionality such as making post request
def test_api_prediction(client, image, model_input_size):
    # use the data dictionary to represent the form input
    data = {}
    # and instead of using pillow, we will use the classic way of getting the image
    with open(f'{image_dir}/{image}', 'rb') as f:
        data['image'] = (io.BytesIO(f.read()), image)

    data['model'] = model_input_size    # put the model data as well

    res = client.post('/predict', data=data, content_type='multipart/form-data')    # make post request
    
    # check if the response succeed
    assert res.status_code == 200

    # and check the prediction is correct by literally checking it is inside the data
    assert image.split('.')[0].capitalize().encode() in res.data


# test the sign up page, check for both valid and invalid email and password
@pytest.mark.parametrize('email', ['ligma@ballz.co', 'a@b.c', 'ayy@lmao.muta'])
@pytest.mark.parametrize('password', ['Abc12345^'])
@pytest.mark.api    # testing the sign up api
def test_signup_api(client, email, password):

    # construct the data
    data = {
        'email' : email,
        'password' : password,
        'confirm' : password
    }

    res = client.post('/signup', data=data, follow_redirects=True)  # redirect the "user" back to the home page

    # first assert that status code is 200
    assert res.status_code == 200

    # get the soup
    soup = make_soup(res.data)

    # first, check that the sign in is successful by checking if is in the home page and has the home, search, setting, and logout in the nav bar
    assert soup.title.text == 'Home'
    links = soup.find_all('a', {'class' : 'nav-link'})
    link_names = ['Home', 'Search', 'Setting', 'Logout']

    # and then for each link content extract, check if is what you will see in a logged in home page
    for i, link in enumerate(links):
        assert link.contents[0] == link_names[i]
    
    # lastly, check the database to see if the newly created user is in there
    user = User.query.filter_by(email=email).first()

    # then check if the user exists, and check if password is the same as well
    assert bool(user) and user.password == password


# now test for the expected failure, test for invalid emails as well as duplicated emails
@pytest.mark.parametrize('email', ['', 'amazing bowls', 'test@test.com', 'meg@vonia', 'gg.com'])
@pytest.mark.parametrize('password', ['', 'leningrad', 'H3il!', 'OmFg12345', 'Abc12345%'])
@pytest.mark.parametrize('confirm', ['', 'leningrad', 'H3il!', 'OmFg12345', 'Abc12345%'])
@pytest.mark.xfail(strict=True)
@pytest.mark.api    # testing for expected fail for the sign up api
def test_xfail_signup_api(client, email, password, confirm):
    # construct the data
    data = {
        'email' : email,
        'password' : password,
        'confirm' : confirm
    }

    res = client.post('/signup', data=data, follow_redirects=True)  # redirect the "user" back to the home page, but it shouldn't for this case

    # get the soup
    soup = make_soup(res.data)

    # first, expect that the sign in is unsuccessful by checking if is in the home page
    assert soup.title.text == 'Home'

    # and I expect it to be in the sign up page still, so check the errors
    error = soup.find('div', {'id' : 'error'}).contents

    # if no error, there shouldn't be one
    assert error is not None
    
    # lastly, check the database to see if the user created is in there
    user = User.query.filter_by(email=email).first()

    # by right, they shouldn't be in there, or have password mismatch
    assert bool(user) and user.password == password


# test the sign in, with the account created in the conftest
@pytest.mark.api
def test_signin_api(client):

    data = {
        'email' : 'test@test.com',
        'password' : 'Test12345$'
    }

    res = client.post('/signin', data=data, follow_redirects=True)

    # first assert that status code is 200
    assert res.status_code == 200

    # get the soup
    soup = make_soup(res.data)

    # check that the sign in is successful by checking if is in the home page and has the home, search, setting, and logout in the nav bar
    assert soup.title.text == 'Home'
    links = soup.find_all('a', {'class' : 'nav-link'})
    link_names = ['Home', 'Search', 'Setting', 'Logout']

    # and then for each link content extract, check if is what you will see in a logged in home page
    for i, link in enumerate(links):
        assert link.contents[0] == link_names[i]


# now test the sign in that are expected to fail
@pytest.mark.parametrize('email', ['', 'obamo', 'test@test.com', 'my@x.com'])
@pytest.mark.parametrize('password', ['', 'nO', 'Test12345$', 'ABc12345^%'])
@pytest.mark.xfail(strict=True)
@pytest.mark.api
def test_xfail_signin_api(client, email, password):

    # before moving on, if skip the test if the email and password is the correct one
    if email == 'test@test.com' and password == 'Test12345$':
        pytest.skip('Correct sign in credential but this should be doing expected fail instead')
    
    # construct the data
    data = {
        'email' : email,
        'password' : password
    }
    res = client.post('/signin', data=data, follow_redirects=True)  

    # get the soup
    soup = make_soup(res.data)

    # first, expect that the sign in is unsuccessful by checking if is in the home page
    assert soup.title.text == 'Home'

    # and same as the signup
    error = soup.find('div', {'id' : 'error'}).contents

    # if no error, there shouldn't be one
    assert error is not None
    
    # just to confirm that the user isn't in the database, check the query
    user = User.query.filter_by(email=email).first()

    # by right, they shouldn't be in there, or have password mismatch
    assert bool(user) and user.password == password


# test the editing of the email, with the authenticated client
@pytest.mark.api
@pytest.mark.parametrize('current_email', ['test@test.com'])
@pytest.mark.parametrize('new_email', ['o@a.c', 'NOO@WHAT.cow'])
def test_editing_email_api(authenticated_client, current_email, new_email):
    data = {
        'current_email' : current_email,
        'new_email' : new_email
    }

    res = authenticated_client.post('/changeEmail', data=data, follow_redirects=True)

    assert res.status_code == 200

    soup = make_soup(res.data)

    # get success message and then assert it
    success_msg = soup.find('div', {'id' : 'success'}).contents[0]
    assert 'Email changed successfully' in success_msg


# now try with all kinds of invalid results
@pytest.mark.api
@pytest.mark.xfail(strict=True)
@pytest.mark.parametrize('current_email', ['test@test.com', 'ohno@gg.com'])
@pytest.mark.parametrize('new_email', ['test@test.com', 'NOO@WHAT.cow', '', 'abc@nowhat', 'gg.com'])
def test_xfail_editing_email_api(authenticated_client, current_email, new_email):
    # if the current email is the same as the in in conftest but the new_email is not, skip those
    if current_email == 'test@test.com' and new_email != 'test@test.com':
        pytest.skip('Gurantee to be a pass')

    data = {
        'current_email' : current_email,
        'new_email' : new_email
    }

    res = authenticated_client.post('/changeEmail', data=data, follow_redirects=True)
    soup = make_soup(res.data)

    # there shouldn't be any success message
    success_msg = soup.find('div', {'id' : 'success'})
    assert bool(success_msg)


# test the editing of the password, with the authenticated client
@pytest.mark.api
@pytest.mark.parametrize('current_password', ['Test12345$'])
@pytest.mark.parametrize('new_password', ['Abc!2124F5', 'NOO@WHAT.cow69'])
def test_editing_password_api(authenticated_client, current_password, new_password):
    data = {
        'current_password' : current_password,
        'new_password' : new_password,
        'new_confirm' : new_password
    }

    res = authenticated_client.post('/changePassword', data=data, follow_redirects=True)

    assert res.status_code == 200

    soup = make_soup(res.data)

    # get success message and then assert it
    success_msg = soup.find('div', {'id' : 'success'}).contents[0]
    assert 'Password changed successfully' in success_msg


# now try with all kinds of invalid results, again
@pytest.mark.api
@pytest.mark.xfail(strict=True)
@pytest.mark.parametrize('current_password', ['Test12345$', '', 'nobruh', 'Abc12345^'])
@pytest.mark.parametrize('new_password', ['Test12345$', 'NOO@WHAT.cow', '', 'Abc12345^', 'gg'])
@pytest.mark.parametrize('new_confirm', ['Test12345$', 'NOO@WHAT.cow', '', 'Abc12345^', 'gg'])
def test_xfail_editing_password_api(authenticated_client, current_password, new_password, new_confirm):
    # if the current password is the same as the in in conftest, but the new password is not, and the new password is the same as the confirm password, skip those
    if current_password == 'Test12345$' and new_password != 'Test12345$' and new_password == new_confirm:
        pytest.skip('Gurantee to be a pass')

    data = {
        'current_password' : current_password,
        'new_password' : new_password,
        'new_confirm' : new_confirm
    }

    res = authenticated_client.post('/changePassword', data=data, follow_redirects=True)
    soup = make_soup(res.data)

    # there shouldn't be any success message
    success_msg = soup.find('div', {'id' : 'success'})
    assert bool(success_msg)


# now test for account deletion
@pytest.mark.api
@pytest.mark.database
def test_account_deletion(authenticated_client):    
    res = authenticated_client.post('/delete_user', follow_redirects=True)
    assert res.status_code == 200

    # and then check that the user doesn't exists anymore
    user = User.query.filter_by(email = 'test@test.com').first()
    assert user is None


# now test with an authenticated client and then attempt to retrieve the history data
@pytest.mark.api      
@pytest.mark.database 
def test_api_prediction_auth(authenticated_client):

    data = {}
    with open('./tests/test_veg_images/carrot.jpg', 'rb') as f:
        data['image'] = (io.BytesIO(f.read()), 'carrot.jpg')

    data['model'] = '128 pixels model'    # put the model data as well

    res = authenticated_client.post('/predict', data=data, content_type='multipart/form-data')    # make post request
    
    # check if the response succeed
    assert res.status_code == 200

    # and check the prediction is correct by literally checking it is inside the data
    assert b'Carrot' in res.data

    # then next attempt to retrieve the history data and check
    history = History.query.get(1)
    
    # and then assert that the highest probability is the carrot
    assert LABELS[np.argmax(history.probs)].lower() == 'carrot'
    # and also assert that the model stored is also correct
    assert int(history.model) == 128


# test for saving, and retrieving
@pytest.mark.api      
@pytest.mark.database
def test_save_retrieve_pred_api(authenticated_client):

    data = {}
    with open('./tests/test_veg_images/carrot.jpg', 'rb') as f:
        data['image'] = (io.BytesIO(f.read()), 'carrot.jpg')

    data['model'] = '128 pixels model'    # put the model data as well

    res = authenticated_client.post('/predict', data=data, content_type='multipart/form-data')    # make post request
    
    # check if the response succeed
    assert res.status_code == 200

    # and check the prediction is correct by literally checking it is inside the data
    assert b'Carrot' in res.data

    # make a get but now to /history/<history_id>
    res2 = authenticated_client.get('/history/1')

    assert res2.status_code == 200
    
    # check no error div
    soup = make_soup(res2.data)
    assert soup.find('div', {'id' : 'error'}) is None
    # again, check the data
    assert b'Carrot' in res2.data


# make a prediction, delete it, and test that it is not there anymore
@pytest.mark.api
@pytest.mark.database
@pytest.mark.parametrize('image', images)
@pytest.mark.parametrize('model_input_size', ['128 pixels model', '31 pixels model'])
def test_make_pred_delete(authenticated_client, image, model_input_size):
    # merely an extension of one of the previous test
    data = {}
    with open(f'{image_dir}/{image}', 'rb') as f:
        data['image'] = (io.BytesIO(f.read()), image)

    data['model'] = model_input_size    
    res = authenticated_client.post('/predict', data=data, content_type='multipart/form-data')    # make post request
    
    # check if the response succeed
    assert res.status_code == 200

    # and check the database to see if the data is there, it MUST be there
    history = History.query.get(1)
    
    # and then assert that the highest probability is the correct one
    assert LABELS[np.argmax(history.probs)].lower() == image.split('.')[0].lower()
    
    # and now attempt to delete it with the api
    res2 = authenticated_client.post(f'/delete_history/1', follow_redirects=True)

    # check again
    assert res2.status_code == 200

    # now check the database, it should be a none now
    history2 = History.query.get(1)
    
    # and then assert that the highest probability is the correct one
    assert history2 == None