from flask import Blueprint, redirect, url_for, render_template, flash, request
from flask_login import current_user, login_required, login_user, logout_user
import base64
from io import BytesIO
from .. import bcrypt
from werkzeug.utils import secure_filename
from ..forms import RegistrationForm, LoginForm, UpdateUsernameForm, UpdateProfilePicForm
from ..models import User

users = Blueprint("users", __name__)

""" ************ User Management views ************ """

# TODO: implement
@users.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('movies.index'))

    form = RegistrationForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            user = User(username=form.username.data, email=form.email.data, password=hashed_password)
            user.save()
            return redirect(url_for('users.login'))
    return render_template('register.html', form=form)


# TODO: implement
@users.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('songs.index'))

    form = LoginForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            user = User.objects(username=form.username.data).first()

            if user is not None and bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('users.account')) # May have to add parameters
            else:
                flash("Failed to log in!")
    return render_template('login.html', form=form)

# TODO: implement
@users.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('songs.index'))


@users.route("/account", methods=["GET", "POST"])
@login_required
def account():
    update_username_form = UpdateUsernameForm()
    update_profile_pic_form = UpdateProfilePicForm()
    if request.method == "POST":
        if update_username_form.submit_username.data and update_username_form.validate():
            #user = User.objects(username=current_user.username).first()
            current_user.modify(username=update_username_form.username.data)
            current_user.save()
            #Modify needed
        if update_profile_pic_form.submit_picture.data and update_profile_pic_form.validate():
            image = update_profile_pic_form.picture.data
            filename = secure_filename(image.filename)
            content_type = f'images/{filename[-3:]}'
            if current_user.profile_pic.get() is None:
                # user doesn't have a profile picture => add one
                current_user.profile_pic.put(image.stream, content_type=content_type)
            else:
            # user has a profile picture => replace it
                current_user.profile_pic.replace(image.stream, content_type=content_type)
            current_user.save()
            #Modify needed
            
    # TODO: handle get requests
    if current_user.profile_pic.get() is None:
        return render_template('account.html',image = None, update_username_form = update_username_form, update_profile_picture_form = update_profile_pic_form)
    else:
        user = User.objects(username=current_user.username).first()
        profile_pic_bytes = BytesIO(user.profile_pic.read())
        profile_pic_base64 = base64.b64encode(profile_pic_bytes.getvalue()).decode()
        return render_template('account.html',image = profile_pic_base64, update_username_form = update_username_form, update_profile_picture_form = update_profile_pic_form)
    