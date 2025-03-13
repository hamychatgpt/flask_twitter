from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from twitter_analyzer.models.user import User

class LoginForm(FlaskForm):
    """فرم ورود به سیستم"""
    username = StringField('نام کاربری', validators=[DataRequired(message='این فیلد الزامی است')])
    password = PasswordField('رمز عبور', validators=[DataRequired(message='این فیلد الزامی است')])
    remember_me = BooleanField('مرا به خاطر بسپار')
    submit = SubmitField('ورود')

class RegistrationForm(FlaskForm):
    """فرم ثبت‌نام"""
    username = StringField('نام کاربری', validators=[
        DataRequired(message='این فیلد الزامی است'),
        Length(min=3, max=25, message='نام کاربری باید بین 3 تا 25 کاراکتر باشد')
    ])
    email = StringField('ایمیل', validators=[
        DataRequired(message='این فیلد الزامی است'),
        Email(message='لطفاً یک آدرس ایمیل معتبر وارد کنید')
    ])
    password = PasswordField('رمز عبور', validators=[
        DataRequired(message='این فیلد الزامی است'),
        Length(min=6, message='رمز عبور باید حداقل 6 کاراکتر باشد')
    ])
    confirm_password = PasswordField('تکرار رمز عبور', validators=[
        DataRequired(message='این فیلد الزامی است'),
        EqualTo('password', message='رمز عبور و تکرار آن باید یکسان باشند')
    ])
    submit = SubmitField('ثبت‌نام')
    
    def validate_username(self, username):
        """اعتبارسنجی نام کاربری - بررسی تکراری نبودن"""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('این نام کاربری قبلاً استفاده شده است. لطفاً نام کاربری دیگری انتخاب کنید.')
    
    def validate_email(self, email):
        """اعتبارسنجی ایمیل - بررسی تکراری نبودن"""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('این آدرس ایمیل قبلاً استفاده شده است. لطفاً آدرس ایمیل دیگری وارد کنید.')
