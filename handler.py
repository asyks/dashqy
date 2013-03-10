
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
from metrics_objects import *

path = os.path.dirname(__file__)
templates = os.path.join(path, 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(templates), autoescape=True) 

decorator = OAuth2Decorator(
	client_id='1048565728869.apps.googleusercontent.com',
	client_secret='7UniAw2jEuomwSpRpRI5kbzz',
  scope=['https://www.googleapis.com/auth/analytics.readonly',
         'https://www.googleapis.com/auth/dfareporting'])

gamgmt = GaMgmt(decorator)
dubClick = DoubleClick(decorator)

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

class Home(Handler):

  def get(self):
    self.write('the home page')
    ## self.render('home.html', **self.params)

class GaManagement(Handler): 

  @decorator.oauth_aware
  def render_page(self,accountId=None,propertyId=None,profileId=None):
    self.params['profileId'] = profileId
    if decorator.has_credentials():
      if accountId:
        if propertyId:
          self.fetch_profiles(accountId, propertyId)
        else:
          self.fetch_properties(accountId)
      else:
        self.fetch_accounts()
      logging.warning(profileId)
      logging.warning(self.params['profileId'])
      self.render('ga1.html', **self.params)
    else:
      url = decorator.authorize_url()
      self.redirect(url)

  def fetch_accounts(self):
    try:
      accountList = list()
      gamgmt.get_accounts(accountList)
      self.params['accountList'] = accountList 
    except TypeError, error:
      print 'There was a type error: %s' % error

  def fetch_properties(self, accountId):
    try:
      propertyList = list()
      gamgmt.get_properties(propertyList, accountId)
      self.params['accountId'] = accountId
      self.params['propertyList'] = propertyList
    except TypeError, error:
      print 'There was a type error: %s' % error

  def fetch_profiles(self, accountId, propertyId):
    try:
      profileList = list()
      segmentList = list()
      gamgmt.get_profiles(profileList, accountId, propertyId)
      gamgmt.get_segments(segmentList)
      self.params['propertyId'] = propertyId
      self.params['profileList'] = profileList
      self.params['segmentList'] = segmentList
    except TypeError, error:
      print 'There was a type error: %s' % error

  def get(self):
    self.render_page()

  def post(self):
    accountId = self.request.get('accountId') or None
    propertyId = self.request.get('propertyId') or None
    profileId = self.request.get('profileId') or None
    self.render_page(accountId, propertyId, profileId)

class GaMetrics(Handler):

  @decorator.oauth_aware
  def get(self):
    profileId = self.request.get('profileId')
    logging.warning(profileId)
    self.params['profileId'] = profileId
    self.render('ga1.html', **self.params)

  def post(self):
    profileId = self.request.get('profileId')
    logging.warning(profileId)
    metrics = self.request.get_all('metrics')
    dateRange = int(self.request.get('dateRange'))
    segmentId = self.request.get('segmentId') or None

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

    try:
      results = gamgmt.get_results(profileId, 
                                   startDate, 
                                   endDate, 
                                   metricLabel,
                                   segmentId)
      self.params['results'] = results.get('totalsForAllResults')
      self.params['profileId'] = results.get('profileInfo') \
                                       .get('profileId')
      self.params['profileName'] = results.get('profileInfo') \
                                          .get('profileName')
      self.render('ga2.html', **self.params)
    except TypeError, error:
      print 'There was a type error: %s' % error

  def poster(self):
    path = '/gametrics'
    accountId = self.request.get('accountId')
    propertyId = self.request.get('propertyId')
    profileId = self.request.get('profileId')
    redirectUrl = path + '?propertyId=' + propertyId \
                  + "&accountId=" +  accountId \
                  + "&profileId=" +  profileId
    self.redirect(redirectUrl)

class DashOne(Handler):

  @decorator.oauth_aware
  def get(self):
    if decorator.has_credentials():
      profileId = str(57024164)
      segmentId = str(1947454746)
      metrics = ['visitors',
                 'visits',
                 'bounces',
                 'visitBounceRate',
                 'timeOnSite']
      metricLabel = 'ga:'
      metricLabel += (',' + metricLabel).join(metrics)
      startDate = endDate = date.today()
      startDate -= timedelta(days=15)
      endDate -= timedelta(days=1)
      startDate = startDate.strftime("%Y-%m-%d")
      endDate = endDate.strftime("%Y-%m-%d")
      try:
        results = gamgmt.get_results(profileId, 
                                   startDate, 
                                   endDate, 
                                   metricLabel,
                                   segmentId)
        self.params['results'] = results.get('totalsForAllResults')
        self.params['profileId'] = results.get('profileInfo') \
                                 .get('profileId')
        self.params['profileName'] = results.get('profileInfo') \
                                   .get('profileName')
        self.render('ga2.html', **self.params)
      except TypeError, error:
        print 'There was a type error: %s' % error
    else:
      url = decorator.authorize_url()
      self.redirect(url)

class DcSandbox(Handler): 

  @decorator.oauth_aware
  def render_page(self, profileId=None, metricsList=None):
    if decorator.has_credentials():
      if metricsList:
        self.fetch_metrics(profileId, metricsList)
      elif profileId:
        self.fetch_reportList(profileId)
      else:
        self.fetch_profiles()
      self.render('dc1.html', **self.params)
    else:
      url = decorator.authorize_url()
      self.redirect(url)

  def fetch_profiles(self):
    try:
      profileList = list()
      dubClick.get_profiles(profileList) 
      self.params['profileList'] = profileList 
      self.params['metrics'] = dfaMetrics
    except TypeError, error:
      print 'There was a type error: %s' % error

  def fetch_reportList(self, profileId):
    try:
      reportList = list()
      dubClick.get_reportList(profileId, reportList)
      logging.warning(reportList) 
    except TypeError, error:
      print 'There was a type error: %s' % error

  def fetch_metrics(self, profileId, metricsList):
    try:
      metricList = list()
      startDate = endDate = date.today()
      startDate -= timedelta(days=15)
      endDate -= timedelta(days=1)
      startDate = startDate.strftime("%Y-%m-%d")
      endDate = endDate.strftime("%Y-%m-%d")
      dubClick.get_metrics(profileId=profileId,
                           startDate=startDate,
                           endDate=endDate,
                           dimensionName=metricsList[0]) 
    except TypeError, error:
      print 'There was a type error: %s' % error

  def get(self):
    self.render_page()

  def post(self):
    profileId = self.request.get('profileId')
    metricsList = self.request.get_all('metric-select')
    self.render_page(profileId, metricsList)

class DcMetrics(Handler): 

  @decorator.oauth_aware
  def post(self):
    path = '/dc' 
    accountId = self.request.get('profileId')
    redirectUrl = path + '?profileId=' + profileId
    self.redirect(redirectUrl)

  @decorator.oauth_aware
  def render_metrics(self, profileId):
    try:
      return
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
                               (decorator.callback_path, 
                                decorator.callback_handler()),
                               (r'/ga/?', GaManagement),
                               (r'/ga/metrics/?', GaMetrics),
                               (r'/dc/?', DcSandbox),
                               (r'/dash1/?', DashOne),
                               (r'/logout/?', Logout),
                               (r'/.*', Error)
                              ],
                                debug=True)
