from wtforms import Form, StringField, TextAreaField, PasswordField, validators,BooleanField
from wtforms.fields.html5 import EmailField

class ArticleForm(Form):
    title = StringField('Título',[validators.DataRequired()])
    body = TextAreaField('Cuerpo',[validators.DataRequired()])

class RegisterForm(Form):
    name = StringField('Name',[validators.Length(min=1,max=50)])
    username = StringField('Username',[validators.Length(min=4,max=25)])
    email = EmailField('email',[validators.Length(min=6,max=50),validators.Email()])
    password = PasswordField('Password',[
                validators.DataRequired(),
                validators.EqualTo('confirm',message='Password do not match.')
            ])
    confirm = PasswordField('Confirm password')
    accept_tos = BooleanField('I accept the TOS', [validators.DataRequired()])
