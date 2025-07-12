from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, DateField, PasswordField, SelectField, SubmitField, ValidationError, validators
from wtforms.validators import DataRequired, Email, Length
from datetime import date

def validate_birth(form, field):
    if field.data > date.today():
        raise ValidationError("Некорректная дата рождения")

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', [validators.Length(min=4, max=25)])
    email = StringField('E-mail', [validators.Length(min=6, max=100), validators.Email()])
    password = PasswordField('Пароль', [validators.InputRequired(),
                                        validators.Length(min=6, max=100),
                                        validators.EqualTo('confirm', message='Пароли должны совпадать')])
    confirm = PasswordField('Повторить пароль')
    first_name = StringField('Имя', [validators.Length(min=1, max=100)])
    last_name = StringField('Фамилия', [validators.Length(min=1, max=100)])
    date_of_birth = DateField('Дата рождения', format='%Y-%m-%d', validators=[validators.InputRequired(), validate_birth])
    want_spam = BooleanField('Я согласен(-а) получать рекламную рассылку')
    submit = SubmitField('Зарегистрироваться')

class AdminCreateUserForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=4)])
    first_name = StringField('Имя')
    last_name = StringField('Фамилия')
    date_of_birth = DateField('Дата рождения')
    want_spam = BooleanField('Отправлять новости?')
    role_id = SelectField('Роль', coerce=int)
    submit = SubmitField('Создать пользователя')

class LoginForm(FlaskForm):
    username = StringField('Логин', [validators.InputRequired()])
    password = PasswordField('Пароль', [validators.InputRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class EditUserForm(FlaskForm):
    email = StringField('E-mail', [validators.Length(min=6, max=100), validators.Email()])
    first_name = StringField('Имя', [validators.Length(min=1, max=100)])
    last_name = StringField('Фамилия', [validators.Length(min=1, max=100)])
    date_of_birth = DateField('Дата рождения', format='%Y-%m-%d', validators=[validators.InputRequired()])
    want_spam = BooleanField('Я согласен(-а) получать рекламную рассылку')
    submit = SubmitField('Сохранить')

class AdminEditUserForm(EditUserForm):
    role_id = SelectField('Роль', coerce=int)