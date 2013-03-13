
## google OAuth 2.0 and API imports
import httplib2, uritemplate, gflags, gflags_validators
from apiclient.discovery import build
from oauth2client.appengine import OAuth2Decorator

## standard python library imports
import os, webapp2, jinja2, logging, json, pprint, urllib
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

gaCRpt = GaMgmt(decorator)
dfaRpt = DoubleClick(decorator)

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

class Home(Handler):

  def get(self):
    self.write('the home page')
    ## self.render('home.html', **self.params)

class GaManagement(Handler): 

  def initialize(self, *a, **kw):
    webapp2.RequestHandler.initialize(self, *a, **kw)
    self.user = users.get_current_user()
    if not self.user:
      request_uri = self.request.uri
      login_url = users.create_login_url('/ga')
      self.redirect(login_url)
    self.params['accountId'] = None
    self.params['propertyId'] = None
    self.params['profileId'] = None

  @decorator.oauth_aware
  def render_page(self):
    if decorator.has_credentials():
      if self.params['propertyId']:
        self.fetch_profiles()
      elif self.params['accountId']:
        self.fetch_properties()
      else:
        self.fetch_accounts()
      self.render('ga1.html', **self.params)
    else:
      url = decorator.authorize_url()
      self.redirect(url)

  def fetch_accounts(self):
    try:
      accountList = list()
      gaCRpt.get_accounts(accountList)
      self.params['accountList'] = accountList 
    except TypeError, error:
      print 'There was a type error: %s' % error

  def fetch_properties(self):
    try:
      propertyList = list()
      gaCRpt.get_properties(propertyList, self.params['accountId'])
      self.params['propertyList'] = propertyList
    except TypeError, error:
      print 'There was a type error: %s' % error

  def fetch_profiles(self):
    try:
      profileList = list()
      segmentList = list()
      gaCRpt.get_profiles(profileList, 
                          self.params['accountId'], 
                          self.params['propertyId'])
      gaCRpt.get_segments(segmentList)
      self.params['profileList'] = profileList
      self.params['segmentList'] = segmentList
    except TypeError, error:
      print 'There was a type error: %s' % error

  def get(self):
    self.render_page()

  def post(self):
    self.params['accountId'] = self.request.get('accountId') or None
    self.params['propertyId'] = self.request.get('propertyId') or None
    self.params['profileId'] = self.request.get('profileId') or None
    self.render_page()

class GaMetrics(Handler):

  @decorator.oauth_aware
  def get(self):
    profileId = self.request.get('profileId')
    self.params['profileId'] = profileId
    self.render('ga1.html', **self.params)

  def post(self):
    profileId = self.request.get('profileId')
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
      results = gaCRpt.get_results(profileId, 
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
        results = gaCRpt.get_results(profileId, 
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

  def initialize(self, *a, **kw):
    webapp2.RequestHandler.initialize(self, *a, **kw)
    self.user = users.get_current_user()
    if not self.user:
      request_uri = self.request.uri
      login_url = users.create_login_url('/ga')
      self.redirect(login_url)
    self.params['metrics'] = dfaMetrics
    self.params['profileId'] = None
    self.params['reportId'] = None
    self.params['fileId'] = None
    self.params['fileObj'] = None

  @decorator.oauth_aware
  def render_page(self):
    if decorator.has_credentials():
      if self.params['fileObj']:
        self.fetch_csv()
      if self.params['fileId']:
        self.fetch_file()
      elif self.params['reportId']:
        self.fetch_fileList()
      elif self.params['profileId']:
        self.fetch_reportList()
      else:
        self.fetch_profiles()
      self.render('dc2.html', **self.params)
    else:
      url = decorator.authorize_url()
      self.redirect(url)

  def fetch_profiles(self):
    try:
      profileList = list()
      dfaRpt.get_profiles(profileList) 
      self.params['profileList'] = profileList 
    except TypeError, error:
      print 'There was a type error: %s' % error

  def fetch_reportList(self):
    try:
      reportList = list()
      dfaRpt.get_reportList(self.params['profileId'],
        reportList)
      self.params['reportList'] = reportList
    except TypeError, error:
      print 'There was a type error: %s' % error

  def fetch_report(self):
    try:
      report = list()
      response = dfaRpt.get_report(self.params['profileId'],
        self.params['reportId'],
        report)
      self.params['report'] = report
    except TypeError, error:
      print 'There was a type error: %s' % error

  def fetch_fileList(self):
    try:
      files = list()
      dfaRpt.get_fileList(self.params['profileId'],
        self.params['reportId'],
        files)
      self.params['files'] = files 
    except TypeError, error:
      print 'There was a type error: %s' % error

  def fetch_file(self):
    try:
      fileObj = dict()
      response = dfaRpt.get_file(self.params['profileId'],
        self.params['reportId'],
        self.params['fileId'],
        fileObj)
      self.params['fileObj'] = fileObj
    except TypeError, error:
      print 'There was a type error: %s' % error

  def fetch_csv(self):
#    body = urllib.urlencode({'access_toke':  \
#     decorator.credentials.access_token})
#    http = httplib2.Http()
    http = decorator.http()
    response, content = http.request('https://storage.googleapis.com/dfa_-17f5a4e8dd95cd214c8159f5678d67bc08f77034/636_query_20130312_003243_1850705.csv', method='GET')
    logging.warning(response)
    logging.warning(content)

  def fetch_metrics(self):
    try:
      metricList = list()
      startDate = endDate = date.today()
      startDate -= timedelta(days=15)
      endDate -= timedelta(days=1)
      startDate = startDate.strftime("%Y-%m-%d")
      endDate = endDate.strftime("%Y-%m-%d")
      dfaRpt.get_metrics(profileId=self.params['profileId'],
        startDate=startDate,
        endDate=endDate,
        dimensionName=self.params['metricList'][0]) 
    except TypeError, error:
      print 'There was a type error: %s' % error

  def get(self):
    self.render_page()

  def post(self):
    self.params['profileId'] = self.request.get('profileId') or None
    self.params['reportId'] = self.request.get('reportId') or None
    self.params['fileId'] = self.request.get('fileId') or None
    self.render_page()

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
