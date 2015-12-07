import arrow

from flask import (
    # Blueprint,
    # url_for,
    redirect,
    request,
    current_app,
    g,
    abort,
    )

from sqlalchemy.orm.exc import NoResultFound

from app import db
from app.models import (
    User,
    )
from . import version


app = version.Blueprint('user', __name__, url_prefix='/user')


@app.route('/auth', methods=['POST'])
def auth():
    try:
        user = User.query.filter(User.username == request.args['username'])
        if request.args['password'] == user.password:
            return "ok"
    except KeyError:
        return "bad request"
    except NoResultFound:
        pass

    return "fail"


# @app.route('/login', methods=['GET'])
# def login():
#     return render_template('user/login.jinja.html')


# @app.route('/login', methods=['POST'])
# def do_login():
#     try:
#         user = User.query.filter(User.username.like(request.form.get('username'))).one()
#         if user.check_password(request.form.get('password')):
#             g.session['user'] = user
#             return redirect(url_for('index.index'))
#     except NoResultFound:
#         pass

#     if 'user' in g.session:
#         del g.session['user']
#     flash('Invalid username or password.', 'danger')
#     return redirect(url_for('.login'))


# @app.route('/logout', methods=['GET'])
# def logout():
#     if 'user' in g.session:
#         csrf = request.args.get('csrf')
#         if csrf and g.session.csrf(csrf):
#             del g.session['user']
#             flash('You are now logged out.', 'info')
#         else:
#             abort(403)
#     return redirect(url_for('user.login'))


# @app.route('/signup', methods=['GET', 'POST'])
# def signup():
#     form = SignupForm()

#     if request.method == 'POST' and form.validate():
#         user = User(
#             username=form.username.data,
#             email=form.email.data,
#             direct_roles=Role.get_default_roles()
#         )
#         user.set_password(form.password.data)
#         db.session.add(user)
#         db.session.commit()
#         if current_app.config.get('REQUIRE_EMAIL_VERIFICATION'):
#             user.start_verification()
#             db.session.add(user)
#             db.session.commit()
#             EmailMessage(
#                 current_app.config.get('SITE_NAME') + ' E-Mail Verification',
#                 user.email,
#                 **render_email_multipart(
#                     'user/verify_email',
#                     user=user
#                 )
#             ).send()
#             flash('A confirmation email has been sent to the address you provided with instructions to verify your email.', 'info')
#         else:
#             flash('Your account has been created and you may now log in.', 'success')

#         return redirect(url_for('user.login'))

#     return render_template('user/signup.jinja.html', form=form)


# @app.route('/verify_email/{code}', methods=['GET'])
# def verify_email(code):
#     try:
#         user = User.query.filter(User.email_verification_code == code).one()
#         if user.email_verification_expiration < arrow.utcnow():
#             flash('Your e-mail verification code has expired.  Please attempt a password reset to continue.', 'danger')
#         else:
#             user.email_verification_code = None
#             user.email_verification_expiration = None
#             db.session.commit()
#             flash('Your e-mail address is now verified and you can log in.', 'success')
#     except NoResultFound:
#         flash('The verification code you have provided is not valid.', 'danger')

#     return redirect(url_for('user.login'))
