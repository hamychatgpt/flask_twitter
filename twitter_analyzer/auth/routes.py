from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse  # این درست است - از urlparse استفاده می‌کنیم
from . import auth_bp
from .forms import LoginForm, RegistrationForm
from twitter_analyzer.models.user import User
from twitter_analyzer.models import db

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """مسیر ورود به سیستم"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('نام کاربری یا رمز عبور نادرست است', 'error')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':  # اینجا تغییر کرد از url_parse به urlparse
            next_page = url_for('dashboard.index')
        flash('با موفقیت وارد شدید!', 'success')
        return redirect(next_page)
    
    return render_template('auth/login.html', title='ورود به سیستم', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """مسیر ثبت‌نام"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('ثبت‌نام شما با موفقیت انجام شد! اکنون می‌توانید وارد شوید.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='ثبت‌نام', form=form)

@auth_bp.route('/logout')
def logout():
    """مسیر خروج از سیستم"""
    logout_user()
    flash('با موفقیت از سیستم خارج شدید.', 'info')
    return redirect(url_for('dashboard.index'))


