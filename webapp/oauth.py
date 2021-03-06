import json
import requests
import logging
from uuid import uuid4
from flask import Blueprint
from flask import Flask, current_app
from flask import render_template
from flask import request
from flask import Response
from flask import session
from flask import redirect
from flask import url_for
from database import Database
from user import User

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(filename)s ## [%(asctime)s] -- %(levelname)s == "%(message)s"')
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

oauth = Blueprint('oauth', __name__,)

app = Flask(__name__)
with app.app_context():
    current_app = app
    mongo_curs = Database().init_mongo(app)

##########################################################################
# OAuth
##########################################################################
@oauth.route('/login')
def login():   
    return render_template('methods/login.html')

@oauth.route('/grant', methods=['GET'])
def grant():
    grant_host_url = os.environ['GRANT_HOST_URL']
    redirect_uri_conf = os.environ['REDIRECT_URI']

    grant_url = grant_host_url + "/auth/authorize" + \
                "?response_type=code" + \
                "&state=" + str(uuid4().hex) + \
                "&client_id=pytheas" + \
                "&redirect_uri=" + redirect_uri_conf

    headers = {
        'Location': grant_url
    }

    return Response(grant_url, status=302, headers=headers)

@oauth.route('/auth', methods=['GET'])
def auth():
    code = str(request.args['code']) 
    state = str(request.args['state'])
    
    redirect_uri_conf = os.environ['REDIRECT_URI']
    grant_host_url = os.environ['GRANT_HOST_URL']

    payload = {
      'code': code,
      'state': state,
      'client_id': 'pytheas',
      'client_secret': 'mys3cr3t',
      'redirect_uri': redirect_uri_conf,
      'grant_type': 'authorization_code'
    }

    r_grant = requests.post(grant_host_url + '/auth/grant', data=payload)
    data = r_grant.json()

    if 'access_token' in data:
        r_access = requests.get(grant_host_url + '/auth/access?access_token=' + str(data['access_token']))
        logger.debug(r_access.json())
    else:
        logger.debug('bad access token')
        return redirect(url_for('/'))

    session['access_token'] = data['access_token']
    session['profil'] = r_access.json()

    current_user = User(mongo_curs)
    current_user.create_or_replace_user_cortext(r_access)

    return redirect(url_for('home'))