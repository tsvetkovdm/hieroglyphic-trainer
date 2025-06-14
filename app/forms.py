from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, DateField, IntegerField, PasswordField, SubmitField, validators

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', [validators.Length(min=4, max=25)])
    email = StringField('E-mail', [validators.Length(min=6, max=100), validators.Email()])
    password = PasswordField('Пароль', [validators.InputRequired(),
                                        validators.Length(min=6, max=100),
                                        validators.EqualTo('confirm', message='Пароли должны совпадать')])
    confirm = PasswordField('Повторить пароль')
    first_name = StringField('Имя', [validators.Length(min=1, max=100)])
    last_name = StringField('Фамилия', [validators.Length(min=1, max=100)])
    date_of_birth = DateField('Дата рождения', format='%Y-%m-%d', validators=[validators.InputRequired()])
    want_spam = BooleanField('Я согласен(-а) получать рекламную рассылку', [validators.InputRequired()])
    submit = SubmitField('Зарегистрироваться')

class EditUserFrom(FlaskForm):
    email = StringField('E-mail', [validators.Length(min=6, max=100), validators.Email()])
    first_name = StringField('Имя', [validators.Length(min=1, max=100)])
    last_name = StringField('Фамилия', [validators.Length(min=1, max=100)])
    date_of_birth = DateField('Дата рождения', format='%Y-%m-%d', validators=[validators.InputRequired()])
    want_spam = BooleanField('Я согласен(-а) получать рекламную рассылку', [validators.InputRequired()])
    submit = SubmitField('Сохранить')