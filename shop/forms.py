from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, validators
from wtforms import TextAreaField, SelectField, FloatField, IntegerField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp
from wtforms.validators import InputRequired
import re

class RegistrationForm(FlaskForm):
    name = StringField('Your Username', validators=[DataRequired()])
    email = StringField('Your Email', validators=[DataRequired(), validators.Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Repeat your password', validators=[DataRequired(), EqualTo('password')])
    agree_terms = BooleanField('I agree all statements in', validators=[DataRequired()])


class Loginform(FlaskForm):
    name = StringField('Your Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class AddProductForm(FlaskForm):
    name = StringField('Product Name', validators=[InputRequired()], render_kw={'style': 'background-color: #ffffff; color: #000000;'})
    description = TextAreaField('Description', validators=[InputRequired()], render_kw={'style': 'background-color: #ffffff; color: #000000;'})
    category = SelectField('Category', choices=[
        ('Fresh Produce', 'Fresh Produce'),
        ('Snack and Candy', 'Snack and Candy'),
        ('Pantry Staples', 'Pantry Staples'),
        ('Gourmet Foods', 'Gourmet Foods'),
        ('Beverages', 'Beverages')
    ], render_kw={'style': 'background-color: #ffffff; color: #000000;'})
    price = FloatField('Price', render_kw={'style': 'background-color: #ffffff; color: #000000;'})
    stock = IntegerField('Units In Stock', render_kw={'style': 'background-color: #ffffff; color: #000000;'})
    product_image = FileField('Product Image', validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')])

def remove_commas(form, field):
    if field.data:
        field.data = re.sub(r'[^\d]', '', field.data)

class AddProfile(FlaskForm):
    name = StringField('Enter Full Name', validators=[InputRequired()])
    phone = StringField('Enter Phone Number', validators=[InputRequired()])
    product_image = FileField('Product Image', validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')])
    adinfo = StringField('Enter Additional Information', validators=[InputRequired(), Regexp(r'^[a-zA-Z\s]*$')])
    street = StringField('Enter Street', validators=[InputRequired()])
    city = StringField('Enter City', validators=[InputRequired()])
    state = StringField('Enter State', validators=[InputRequired()])
    zip = StringField('Enter Zip Code', validators=[InputRequired()])


class change_pass(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Repeat your password', validators=[DataRequired(), EqualTo('password')])