import os

from flask import Flask, render_template, request, flash, redirect, session, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from forms import UserAddForm, LoginForm, MessageForm, EditUserForm, TokenForm
from models import db, connect_db, User, Message, LikedMessage

CURR_USER_KEY = "curr_user"  # value: user.id

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgres:///warbler'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True

# "it's a secret" - set for development
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
toolbar = DebugToolbarExtension(app)

connect_db(app)


##############################################################################
# User signup/login/logout


@app.before_request
def add_user_to_g():
    # import pdb; pdb.set_trace()

    print('session', session)
    """If we're logged in, add curr user to Flask global."""
    # global data within a part context
    # g is global dictionary that stores user instance info: {user: user_instance}

    # below will run before every single request
    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.add(user)
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""
    
    do_logout()

    flash(f"Successful log out!", "success")

    return redirect("/login")


##############################################################################
# General user routes:

@app.route('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()
    
    form=TokenForm()
    
    return render_template('users/index.html', users=users, form=form)


@app.route('/users/<int:user_id>')
def users_show(user_id):
    """Show user profile."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    user = User.query.get_or_404(user_id)
    form = TokenForm()

    return render_template('users/show.html', user=user, form=form)


@app.route('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of people this user is following."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    form = TokenForm()
    user = User.query.get_or_404(user_id)
    return render_template('users/following.html', user=user, form=form)


@app.route('/users/<int:user_id>/followers')
def users_followers(user_id):
    """Show list of followers of this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = TokenForm()
    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html', user=user, form=form)


@app.route("/users/<int:user_id>/likes")
def user_likes(user_id):
    """Show user's liked messages."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = TokenForm()
    
    user = User.query.get_or_404(user_id)
    messages = user.message_likes

    return render_template('users/likes.html', messages=messages, form=form)



@app.route('/users/follow/<int:follow_id>', methods=['POST'])
def add_follow(follow_id):
    """Add a follow for the currently-logged-in user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.append(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/stop-following/<int:follow_id>', methods=['POST'])
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get(follow_id)
    g.user.following.remove(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/profile', methods=["GET", "POST"])
def profile():
    """Update profile for current user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    # username, password
    # print('***********g.user.id', g.user.id)
    user = User.query.get_or_404(g.user.id)

    form = EditUserForm(obj=user)

    user = User.authenticate(user.username, form.password.data)

    if user and form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.image_url = form.image_url.data
        user.header_image_url = form.header_image_url.data
        user.bio = form.bio.data

        db.session.commit()
        return redirect(f'/users/{g.user.id}')

    else:
        return render_template('users/edit.html', form=form)
    


@app.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete user."""
    #TODO use deleteform()
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = TokenForm()

    if form.validate_on_submit():
        do_logout()

        db.session.delete(g.user)
        db.session.commit()

    return redirect("/signup", form=form)


##############################################################################
# Messages routes:

@app.route('/messages/new', methods=["GET", "POST"])
def messages_add():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")

    return render_template('messages/new.html', form=form)


@app.route('/messages/<int:message_id>', methods=["GET"])
def messages_show(message_id):
    """Show a message."""

    msg = Message.query.get(message_id)
    return render_template('messages/show.html', message=msg)


@app.route('/messages/<int:message_id>/delete', methods=["POST"])
def messages_destroy(message_id):
    """Delete a message."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg = Message.query.get(message_id)
    db.session.delete(msg)
    db.session.commit()

    return redirect(f"/users/{g.user.id}")


##############################################################################
# Homepage and error pages


@app.route('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of followed_users
    """
    
    # user = User.query.get(g.user)
    # print('g.user', User.query.get(g.user.id))
    # print('followers', user.following)

    form = TokenForm()

    if g.user:
        following_id = [user.id for user in g.user.following]

        messages = (Message
                    .query
                    .filter(Message.user_id.in_(following_id))
                    .order_by(Message.timestamp.desc())
                    .limit(100)
                    .all())

        return render_template('home.html', messages=messages, form=form)
    
    return render_template('home-anon.html')


@app.route('/users/<int:msg_id>/like', methods=['POST'])
def like_or_unlike_message(msg_id):
    ''' Handle user liking or unliking a message. Adds user id and msg id to
    liked_messages table if messages is liked. Removes relevant record 
    if message is unliked. 
    
    Redirects to homepage'''

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    form = TokenForm()
    
    if form.validate_on_submit():
        message = Message.query.get(msg_id)
        user = g.user
        #user.likes is an array of the all the message this user likes
        if message in user.message_likes:
            user.message_likes.remove(message) #remove message id from their user's liked message id [])
            db.session.commit()
        else:
            user.message_likes.append(message) #add liked messages to user's liked message list
            db.session.commit()

        return redirect("/")   

    else: 
        return render_template('home.html', form=form)




##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

@app.after_request
def add_header(response):
    """Add non-caching headers on every request."""

    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control
    response.cache_control.no_store = True
    return response
