from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length

from flask_pagedown.fields import PageDownField

class ContentForm(FlaskForm):
    pagedown = PageDownField('Enter your markdown')
    submit = SubmitField('Submit')
