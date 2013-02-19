
## google OAuth 2.0 and API imports
import httplib2, uritemplate, gflags, gflags_validators
from apiclient.discovery import build
from oauth2client.appengine import OAuth2Decorator
## standard python library imports
import os, webapp2, jinja2, logging, json, pprint
from datetime import datetime

## app engine library imports
from google.appengine.api import memcache
from google.appengine.api import users

## pulse class/object imports
## from utility import *
## from datamodel import *

path = os.path.dirname(__file__)
templates = os.path.join(path, 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(templates), autoescape=True) 

decorator = OAuth2Decorator(
  client_id='1048565728869.apps.googleusercontent.com',
  client_secret='7UniAw2jEuomwSpRpRI5kbzz',
  scope='https://www.googleapis.com/auth/calendar')

service = build('calendar', 'v3')

class Handler(webapp2.RequestHandler):

  def write(self, *a, **kw):
    self.response.out.write(*a, **kw)

  def render_str(self, template, **b):
    template = jinja_env.get_template(template)
    return template.render(**b)
 
  def render(self, template, **kw):
    self.write(self.render_str(template, **kw))

  def set_user_cookie(self, val):
    name = 'user_id'
    cookie_val = make_secure_val(val)
    self.response.headers.add_header('Set-Cookie', '%s=%s; Path=/' % (name, cookie_val))
 
  def read_user_cookie(self):
    name = 'user_id'
    cookie_val = self.request.cookies.get(name)
    return cookie_val and check_secure_val(cookie_val) 

  def login(self, user): 
    user_id = str(user.key().id()) 
    self.set_user_cookie(user_id)
    set_user_cache(user_id, user)

  def logout(self):
    self.response.delete_cookie('user_id')
    self.response.delete_cookie('dev_appserver_login')

  def render_json(self, d):
    json_content = 'application/json; charset=utf-8'
    self.response.headers['Content-Type'] = json_content
    logging.warning(d)
    json_text = json.dumps(d, sort_keys=True, indent=4, separators=(',', ': '))
    self.write(json_text)

  params = {} ## params contains key value pairs used by jinja2
    
  def initialize(self, *a, **kw):
    webapp2.RequestHandler.initialize(self, *a, **kw)

    if self.request.url.endswith('.json'):
      self.format = 'json'
    else:
      self.format = 'html'

class Home(webapp2.RequestHandler): ## Handler for Home page requests

  @decorator.oauth_required
  def get(self):
    http = decorator.http()
    request = service.events().list(calendarId='primary')	
    response = request.execute(http=http)
    logging.warning(response)
    ## self.render('home.html', **self.params)

class Logout(Handler): ## Handler for Home page requests

  def get(self):
    self.logout()
    request_uri = self.request.uri
    login_url = users.create_logout_url('/resume')
    self.redirect(login_url)

class Error(Handler): ## Default handler for 404 errors

  def get(self):
    global last_page
    self.write("There's been an error... Woops")

app = webapp2.WSGIApplication([(r'/?', Home),
                               (r'/logout/?', Logout),
                               (decorator.callback_path, decorator.callback_handler()),
                               (r'/.*', Error)
                              ],
                                debug=True)
