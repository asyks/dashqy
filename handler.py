
## google OAuth 2.0 and API imports
import httplib2, uritemplate, gflags, gflags_validators
from apiclient.discovery import build
from oauth2client.appengine import OAuth2Decorator

## standard python library imports
import os, webapp2, jinja2, logging, json, pprint
from datetime import date
from datetime  import timedelta

## app engine library imports
from google.appengine.api import memcache
from google.appengine.api import users

## dashboard class/object imports
## from utility import *
## from datamodel import *
from ga_api_classes import *

path = os.path.dirname(__file__)
templates = os.path.join(path, 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(templates), autoescape=True) 

ga_decorator = OAuth2Decorator(
	client_id='1048565728869.apps.googleusercontent.com',
	client_secret='7UniAw2jEuomwSpRpRI5kbzz',
	scope='https://www.googleapis.com/auth/analytics.readonly')

gamgmt = GaMgmt(ga_decorator)

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

    self.user = users.get_current_user()
    if not self.user:
      request_uri = self.request.uri
      login_url = users.create_login_url('/ga')
      self.redirect(login_url)

    if self.request.url.endswith('.json'):
      self.format = 'json'
    else:
      self.format = 'html'

class Home(webapp2.RequestHandler):

  def get(self):
    self.write('the home page')
    ## self.render('home.html', **self.params)

class GaSandbox(Handler): 

  @ga_decorator.oauth_aware
  def render_accounts(self):
    try:
      accountList = list()
      gamgmt.get_accounts(accountList)
      self.params['accountList'] = accountList 
      self.render('ga1.html', **self.params)
    except TypeError, error:
      print 'There was a type error: %s' % error

  @ga_decorator.oauth_aware
  def render_properties(self, accountId):
    try:
      propertyList = list()
      gamgmt.get_properties(propertyList, accountId)
      self.params['accountId'] = accountId
      self.params['propertyList'] = propertyList
      self.render('ga1.html', **self.params)
    except TypeError, error:
      print 'There was a type error: %s' % error

  @ga_decorator.oauth_aware
  def render_profiles(self, accountId, propertyId):
    try:
      profileList = list()
      gamgmt.get_profiles(profileList, accountId, propertyId)
      self.params['accountId'] = accountId
      self.params['propertyId'] = propertyId
      self.params['profileList'] = profileList
      self.render('ga1.html', **self.params)
    except TypeError, error:
      print 'There was a type error: %s' % error

  @ga_decorator.oauth_aware
  def get(self):
    accountId = self.request.get('accountId')
    propertyId = self.request.get('propertyId')
    path = self.request.path
    logging.warning(path)
    if ga_decorator.has_credentials():
      if accountId:
        if propertyId:
          self.render_profiles(accountId, propertyId)
        else:
          self.render_properties(accountId)
      else:
        self.render_accounts()
    else:
      url = ga_decorator.authorize_url()
      self.redirect(url)

class AccountSelect(Handler): 

  @ga_decorator.oauth_aware
  def post(self):
    path = '/ga' 
    accountId = self.request.get('accountId')
    redirectUrl = path + '?accountId=' + accountId
    self.redirect(redirectUrl)

class PropertySelect(Handler): 

  @ga_decorator.oauth_aware
  def post(self):
    path = '/ga'
    accountId = self.request.get('accountId')
    propertyId = self.request.get('propertyId')
    redirectUrl = path + '?propertyId=' + propertyId \
                  + "&accountId=" +  accountId
    self.redirect(redirectUrl)

class ProfileSelect(Handler): 

  @ga_decorator.oauth_aware
  def post(self):
    path = '/gametrics'
    accountId = self.request.get('accountId')
    propertyId = self.request.get('propertyId')
    profileId = self.request.get('profileId')
    redirectUrl = path + '?propertyId=' + propertyId \
                  + "&accountId=" +  accountId \
                  + "&profileId=" +  profileId
    self.redirect(redirectUrl)

class GaMetrics(Handler):

  @ga_decorator.oauth_aware
  def get(self):
    profileId = self.request.get('profileId')
    self.params['profileId'] = profileId
    self.render('ga1.html', **self.params)

  def post(self):
    profileId = self.request.get('profileId')
    metrics = self.request.get_all('metrics')
    dateRange = int(self.request.get('dateRange'))

    metricLabel = 'ga:'
    metricLabel += (',' + metricLabel).join(metrics)

    startDate = endDate = date.today()
    if dateRange == 1:
      startDate -= timedelta(days=8)
      endDate -= timedelta(days=1)
    elif dateRange == 2:
      startDate -= timedelta(days=31)
      endDate -= timedelta(days=1)
    elif dateRange == 3:
      startDate -= timedelta(days=1)
      endDate -= timedelta(days=91)
    startDate = startDate.strftime("%Y-%m-%d")
    endDate = endDate.strftime("%Y-%m-%d")
    logging.warning(startDate)
    logging.warning(endDate)

    try:
      results = gamgmt.get_results(profileId, 
                                   startDate, 
                                   endDate, 
                                   metricLabel)
      self.params['results'] = results.get('totalsForAllResults')
      self.params['profileId'] = results.get('profileInfo') \
                                       .get('profileId')
      self.params['profileName'] = results.get('profileInfo') \
                                          .get('profileName')
      self.render('ga2.html', **self.params)
    except TypeError, error:
      print 'There was a type error: %s' % error

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
                               (ga_decorator.callback_path, ga_decorator.callback_handler()),
                               (r'/ga/?', GaSandbox),
                               (r'/accountselect/?', AccountSelect),
                               (r'/propertyselect/?', PropertySelect),
                               (r'/profileselect/?', ProfileSelect),
                               (r'/gametrics/?', GaMetrics),
                               (r'/logout/?', Logout),
                               (r'/.*', Error)
                              ],
                                debug=True)
