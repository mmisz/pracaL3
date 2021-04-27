from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request, g

from portal_forum.user_activity.utils import login_my_required
from portal_forum.users.forms import RegistrationForm, LoginForm, UpdateAccountForm
from portal_forum import db, bcrypt
from portal_forum.models import User
from flask_login import login_user, current_user, logout_user
from portal_forum.users.utils import save_image

users = Blueprint('users', __name__)

@users.route('/register', methods=['GET', 'POST'])
def register():
    if User.query.filter_by(is_admin=True).first() is None:
        hashed_password = bcrypt.generate_password_hash("admin123").decode('utf-8')
        admin = User(username="Admin", email="true.admin@mail.com", password=hashed_password, is_admin=True)
        db.session.add(admin)
        db.session.commit()
    if current_user.is_authenticated:
        return redirect(url_for('main.forum'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, is_admin=False)
        db.session.add(user)
        db.session.commit()
        flash('Twoje konto utworzono pomyślnie!', 'success')
        return redirect(url_for('users.login'))

    return render_template('register.html', title="Rejestracja", form=form)


@users.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.forum'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.forum'))
        else:
            flash('Wprowadzono niepoprawne dane', 'danger')
    return render_template('login.html', title="Logowanie", form=form)


@users.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.forum'))


@users.route('/account', methods=['GET', 'POST'])
@login_my_required
def account():
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            image_file = save_image(form.picture.data)
            current_user.image_file = image_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Twoje dane zostały zaktualizowane', 'success')
        return redirect(url_for('users.account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    return render_template('account.html', title="Konto użytkownika", image_file=image_file, form=form)
