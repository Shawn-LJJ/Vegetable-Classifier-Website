from .forms import ImageForm, SignUpForm, SignInForm, ChangeEmailForm, ChangePasswordForm, SearchForm
from . import routes
from .functions import *
from ..models import User, History
from .. import login_manager
from flask import render_template, request, url_for, redirect, json, jsonify, send_file
from flask_login import login_required, login_user, logout_user, current_user
from PIL import Image
from sqlalchemy.sql import text

# home page
@routes.route('/')
@routes.route('/index')
@routes.route('/home')
def home():
    form = ImageForm()
    return render_template('index.html', title='Home', form=form, errors=None, prediction=None, current_user=current_user)

# sign up page
@routes.route('/signup', methods=['GET'])
def get_signup():
    form = SignUpForm()
    return render_template('signinorup.html', title='Signup', form=form, errors=None, current_user=current_user)

# sign in page
@routes.route('/signin', methods=['GET'])
def get_signin():
    form = SignInForm()
    return render_template('signinorup.html', title='Signin', form=form, errors=None, current_user=current_user)

# setting page
@routes.route('/setting')
@login_required
def setting():
    e_form = ChangeEmailForm()
    p_form = ChangePasswordForm()
    return render_template('setting.html', title='Setting', forms=[e_form, p_form], errors=None, success = None, current_user=current_user)

# search page
@routes.route('/search', methods=['GET'])
@login_required
def search():
    form = SearchForm()
    return render_template('search.html', title='Search', form=form, results=None)

# prediction
@routes.route('/predict', methods=['POST'])
def predict():
    form = ImageForm()
    errors = None
    pred = None

    # check validation, then see how
    if form.validate_on_submit():
        # if no errors, proceed to do check the image size and the model selected, and scale them if needed
        img = Image.open(form.data['image'])                    # convert the data to pillow image object
        model_input_size = int(form.data['model'].split()[0])   # get the model input size

        # first check if the image size matches the model size, if not then perform a resize
        if model_input_size != img.size[0]:
            img = img.resize((model_input_size, model_input_size))

        # now we can send the image to the model server
        pred, probs = make_prediction(model_input_size, img)

        # then check if the user is authenticated, then proceed to store in the database
        if current_user.is_authenticated:

            history = History(
                probs = probs[0],                              # stores list of probabilites as pickle object
                image = img.tobytes(),                      # stores the image data as bytes
                user_id = current_user.id,                  # stores user id, foreign key to the user model
                model = str(model_input_size),              # stores the model used
                highest_prob = max(probs[0]),                  # stores the highest likely probability
                pred = pred                                 # stores the predicted vegetable
            )

            error = add_entry(history)
            if error:
                print(error)
                error = 'Error adding the predicted data into database.'
           
    else:
        # get the errors which will be displayed to the user
        errors = list(form.errors.values())
        print(errors)

    return render_template('index.html', title='Home', form=form, errors=errors, prediction=pred, current_user=current_user)

# create account
@routes.route('/signup', methods=['POST'])
def post_signup():
    form = SignUpForm()
    errors = None

    # validate and then see how
    if form.validate_on_submit():

        # create a new user model object 
        new_user = User(
            email = form.email.data,
            password = form.password.data
        )

        # and then attempt to add it into new row and catch for error
        error = add_entry(new_user)
        # if got error, then stay in the sign up page and display the error
        if error:
            print(error)
            errors = [['Error creating account. Either the email already exists, or something wrong with our server']]
    else:
        # get the errors which will be displayed to the user
        errors = list(form.errors.values())
        print(errors)

    # if got error, then stay in the sign up page and display the error
    if errors:
        return render_template('signinorup.html', title='Signup', form=form, errors=errors, current_user=current_user)
    
    # if no errors, log the new user in and go back to the home page
    login_user(new_user)
    return redirect(url_for('routes.home'))

# log the user in
@routes.route('/signin', methods=['POST'])
def post_signin():
    form = SignInForm()
    
    # there's no other validation other than the input required for sign in, so just get the user
    user = User.query.filter_by(email=form.email.data).first()

    # then check if the user exists, and check if password is the same as well
    if user and user.password == form.password.data:
        # if so, log the user in and go back to the home page
        login_user(user)
        return redirect(url_for('routes.home'))

    return render_template('signinorup.html', title='Signin', form=form, errors=[['Invalid email or password']], current_user=current_user)

# logout stuff, only those logged in can obviously logged out
@routes.route('/signout')
@login_required
def signout():
    logout_user()
    return redirect(url_for('routes.home'))

# update the email
@routes.route('/changeEmail', methods=['POST'])
@login_required
def change_email():
    e_form = ChangeEmailForm()

    # validate the form and then see how
    if e_form.validate_on_submit():
        # first, check if the current email is the correct one
        current_user_email = User.query.get(current_user.id).email
        if current_user_email != e_form.data['current_email']:
            # if there is email mismatch, then error
            error = [['Error, current email does not match with your existing email!']]
            return render_template('/setting.html', title='Setting', forms=[e_form, ChangePasswordForm()], errors=error, success = None, current_user=current_user)
        
        # next, attempt to edit the email. If there's an existing email, there should be an error from the database itself
        error = edit_entry(email=e_form.data['new_email'])
        if error:
            print(error)
            error = [['Error changing email. Either the email already exists, or something wrong with our server']]
            return render_template('/setting.html', title='Setting', forms=[e_form, ChangePasswordForm()], errors=error, success = None, current_user=current_user)
        
    else:
        # get the errors which will be displayed to the user
        errors = list(e_form.errors.values())
        return render_template('/setting.html', title='Setting', forms=[e_form, ChangePasswordForm()], errors=errors, success = None, current_user=current_user)
    
    # if no issue, it should refresh without issue
    return render_template('/setting.html', title='Setting', forms=[e_form, ChangePasswordForm()], errors=None, success = 'Email changed successfully', current_user=current_user)

# update the password
@routes.route('/changePassword', methods=['POST'])
@login_required
def change_password():
    p_form = ChangePasswordForm()

    # validate password
    if p_form.validate_on_submit():
        # first check if the current password matches the existing one
        current_user_pass = User.query.get(current_user.id).password
        if current_user_pass != p_form.data['current_password']:
            error = [['Error, current password does not match with your existing password!']]
            return render_template('/setting.html', title='Setting', forms=[ChangeEmailForm(), p_form], errors=error, success = None, current_user=current_user)
        
        # finally, change the password
        error = edit_entry(password=p_form.data['new_password'])
        if error:
            print(error)
            error = [['Error changing password.']]
            return render_template('/setting.html', title='Setting', forms=[ChangeEmailForm(), p_form], errors=error, success = None, current_user=current_user)

    else:
        errors = list(p_form.errors.values())
        return render_template('/setting.html', title='Setting', forms=[ChangeEmailForm(), p_form], errors=errors, success = None, current_user=current_user)
    
    return render_template('/setting.html', title='Setting', forms=[ChangeEmailForm(), p_form], errors=None, success = 'Password changed successfully', current_user=current_user)

# delete the user
@routes.route('/delete_user', methods=['POST'])
@login_required
def deleteUser():
    # simple just attempt to delete the user
    try:
        # get the user and delete it, and redirect back to the home page
        user = User.query.get(current_user.id)
        db.session.delete(user)
        db.session.commit()
        return redirect(url_for('routes.home'))
    except Exception as error:
        print(error)
        return render_template('/setting.html', title='Setting', forms=[ChangeEmailForm(), ChangePasswordForm()], errors=[['Error: fail to delete account']], success = None, current_user=current_user)
    
# get the history
@routes.route('/history/<history_id>', methods=['GET'])
@login_required
def get_history(history_id):
    # attempt to fetch the history based on the user's own id and the history id inputted
    history = History.query.filter_by(id = history_id, user_id = current_user.id).first()

    text_groups = []      # groups of text to display the user
    error = None

    # now check to see if there's result from the query
    if history is None:
        error = 'Result is not available'   # if the history doesn't exists for this user, then is an error and will be displayed to in the front end
    
    else:
        # get the data and prepare the text to be shown
        probs = history.probs
        text_groups.append({'Predicted vegetable' : LABELS[np.argmax(probs)]})
        text_groups.append({'Probability' : f'{(max(probs) * 100):.2f}%'})

        # get the index sorted by probs
        argsorted = np.argsort(probs)
        text_groups.append({'2nd most probable' : f'{LABELS[argsorted[-2]]} ({(probs[argsorted[-2]] * 100):.2f}%)'})
        text_groups.append({'3rd most probable' : f'{LABELS[argsorted[-3]]} ({(probs[argsorted[-3]] * 100):.2f}%)'})

        # other info
        text_groups.append({'Model used' : f'{history.model} pixels model'})
        text_groups.append({'Predicted time' : f'{history.timestamp}'})

        # and lastly get the image
        image = Image.frombytes(mode='RGB', data=history.image, size=[int(history.model), int(history.model)])
        image.save('application/static/temp.png')

    return render_template('history.html', title='History', text_groups=text_groups, error=error, history_id=history.id)

# get the histories list
@routes.route('/search', methods=['POST'])
@login_required
def post_search():
    form = SearchForm()
    errors = None
    results = []
    
    if form.validate_on_submit():

        # as I will just use the db.session.execute to run an SQL query to get the results, I will piece together some code
        filter_statements = []
        # if the model field is not "Any", then get whatever result and append into the "where" clause of the sql statement
        if form.data['model'] != 'Any':
            data = form.data['model'].split()[0]
            filter_statements.append(f'model = "{data}"')
        
        # same thing for the prediction
        if form.data['prediction'] != 'Any':
            data = form.data['prediction']
            filter_statements.append(f'pred = "{data}"')
        
        # same for probs but filter by if is at least the user specified amount
        if form.data['prob_pred'] != 0:
            filter_statements.append(f'highest_prob >= {form.data["prob_pred"] / 100}')
        
        # and more importantly, must be the current user as well
        filter_statements.append(f'user_id = {current_user.id}')
        
        # join the statement with the and keyword
        joined_statement = ' and '.join(filter_statements)
        
        # now attempt to construct an sql statement that can get the filtered results
        sql = f'select highest_prob, pred, image, model, id from history where ' + joined_statement + ';'
        cursor = db.session.execute(text(sql))

        # fetch all the results and then transform each image data into an Image object and save them temporarily
        raw_results = cursor.fetchall()

        results = []
        for i, raw_result in enumerate(raw_results):
            tmp_img = Image.frombytes(mode='RGB', data=raw_result[2], size=[int(raw_result[3]), int(raw_result[3])])
            tmp_img.save(f'application/static/temp{i + 1}.png')

            # result structure = [image path, model used, prediction, probability, id]
            results.append([f'../static/temp{i + 1}.png', raw_result[3], raw_result[1], round(raw_result[0] * 100, 2), raw_result[4]])

    else:
        errors = list(form.errors.values())

    return render_template('search.html', title='Search', form=form, results=results, errors=errors)

# delete the history entry
@routes.route('/delete_history/<history_id>', methods=['POST'])
@login_required
def deleteHistory(history_id):
    # again, try to just delete the history
    try:
        # get the history and delete it, and then stay in the search page
        history = History.query.get(history_id)
        db.session.delete(history)
        db.session.commit()
        return redirect(url_for('routes.search'))
    except Exception as error:
        # if got error, display the error message
        form = SearchForm()
        errors = [['Error deleting history result']]
        return render_template('search.html', title='Search', form=form, results=None, errors=errors)

# handles error 404
@routes.app_errorhandler(404)
def page_not_found(error):
    msg = 'Error 404: Page not found'
    return render_template('blank.html', title=msg, error=msg, current_user=current_user), 404

# handles error 401
@routes.app_errorhandler(401)
def page_not_found(error):
    msg = 'Error 401: Unauthorised access or action'
    return render_template('blank.html', title=msg, error=msg, current_user=current_user), 401