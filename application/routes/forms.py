from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, EmailField, PasswordField, FloatField
from wtforms.validators import ValidationError, InputRequired, Email, NumberRange
from flask_wtf.file import FileAllowed, FileField, FileRequired
from PIL import Image
from .functions import LABELS

# custom validator to check that the images are capped at 512 by 512 pixels
class ImageSizeValidator(object):
    def __call__(self, form, field):
        # use pillow's image class to "parse" the image data
        img = Image.open(field.data)
        img_size = img.size
        img_size_text = f'Current image size: {img_size[0]} x {img_size[1]} pixels'
        
        # first check that the width and height are the same, which means the image is exactly a square image
        if img_size[0] != img_size[1]:
            raise ValidationError('Error: Image must be exactly a square image! ' + img_size_text)

        # then check if the pixel of the image exceeds the length/height
        if img_size[0] > 512:
            raise ValidationError('Error: Image must not exceed the specified width/height! ' + img_size_text)
        
        # lastly, check if the pixels are smaller than the specified one
        if img_size[0] < 31:
            raise ValidationError('Error: Image must not be below the specified width/height ' + img_size_text)

# checks for both the password strength, and also checking if the confirm password is the same as well
class ValidatePassword(object):
    def __init__(self, fieldname) -> None:
        self.fieldname = fieldname      # gets the field name to check with

    def __call__(self, form, field):
        # first check if the password strength is good enough
        hasLower = hasUpper = hasNumeric = hasSpecial = False

        # loop through each character and see
        for char in field.data:
            if char.isupper(): hasUpper = True
            elif char.islower(): hasLower = True
            elif char.isnumeric(): hasNumeric = True
            elif not char.isalnum(): hasSpecial = True
        
        # and check if is long enough
        isLong = len(field.data) > 7
        if not (isLong and hasLower and hasUpper and hasNumeric and hasSpecial):    # if neither one of these are true, then raise validation error
            raise ValidationError('Error: Password must contain at least 8 characters, has at least one lower, upper, number, and special character')
        
        # lastly, check if the confirmation password is the same
        if field.data != form[self.fieldname].data:
            raise ValidationError('Error: The password do not match with the confirm password')

# check that both the current and new credential are not the same
# unfortunately, the built in validator has EqualTo, but not the opposite
class NotEqualTo(object):
    def __init__(self, fieldname, errorMsg) -> None:
        self.fieldname = fieldname
        self.errorMsg = errorMsg

    def __call__(self, form, field):
        # if both fields have the same value, raise the error
        if form[self.fieldname].data == field.data:
            raise ValidationError(self.errorMsg)
        

# a form for uploading the images, while also selecting the model
class ImageForm(FlaskForm):
    image = FileField('Upload image', validators=[
        FileAllowed(['jpg', 'png'], 'Please upload images only!'),
        FileRequired('Please upload an image!'),
        ImageSizeValidator()])
    model = SelectField('Select model', choices=['128 pixels model', '31 pixels model'], validators=[InputRequired()])
    submit = SubmitField('Predict')

# a form for signup
class SignUpForm(FlaskForm):
    email = EmailField('Email', validators=[InputRequired(), Email('Invalid email address!')])
    password = PasswordField('Password', validators=[InputRequired(), ValidatePassword('confirm')])
    confirm = PasswordField('Confirm password', validators=[InputRequired()])
    submit = SubmitField('Sign up')

# a form for signin
class SignInForm(FlaskForm):
    email = EmailField('Email', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Sign in')

# form for changing email
class ChangeEmailForm(FlaskForm):
    current_email = EmailField('Current Email', validators=[InputRequired(), NotEqualTo('new_email', 'New email must not be the same as the current email')])
    new_email = EmailField('New Email', validators=[InputRequired(), Email('Invalid email address!')])
    submit = SubmitField('Change email')

# form for changing password
class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[InputRequired(), NotEqualTo('new_password', 'New password must not be the same as the current password')])
    new_password = PasswordField('New Password', validators=[InputRequired(), ValidatePassword('new_confirm')])
    new_confirm = PasswordField('Confirm new Password', validators=[InputRequired()])
    submit = SubmitField('Change password')

# form for the search filter
class SearchForm(FlaskForm):
    model = SelectField('Model used', choices=['Any', '128 pixels model', '31 pixels model'], validators=[InputRequired()])
    prediction = SelectField('Predicted type', choices=['Any'] + LABELS, validators=[InputRequired()])
    prob_pred = FloatField('Min. probability', validators=[NumberRange(0, 100, 'Error: Minimum probablity of the prediction must not exceed below 0 or above 100 percent')], default=0)
    submit = SubmitField('Seach')