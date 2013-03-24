
## standard python library imports
import os, sys, inspect

## adding ./lib to python path to allow module imports from that dir
libPath = os.path.split(inspect.getfile(inspect.currentframe()))
libPath = os.path.join(libPath[0],"lib")
libPath = os.path.abspath(libPath)
lib = os.path.realpath(libPath)
if lib not in sys.path:
  sys.path.insert(0, lib)
  sys.path.insert(0, lib)

## google OAuth 2.0 and API imports
from apiclient.discovery import build

class GaMgmt(object): 

  def __init__(self, decorator):
    self.service = build('analytics', 'v3')
    self.decorator = decorator

  def get_accounts(self, accountList):
    accounts = self.service.management().accounts().list()
    http = self.decorator.http()
    response = accounts.execute(http=http)
    for item in response.get('items'):
      account = dict()
      account['id'] = item.get('id')
      account['name'] = item.get('name')
      accountList.append(account)
    
  def get_properties(self, propertyList, accountId):
    properties = self.service.management().webproperties() \
      .list(accountId=accountId)
    http = self.decorator.http()
    response = properties.execute(http=http)
    for item in response.get('items'):
      prop = dict()
      prop['id'] = item.get('id')
      prop['name'] = item.get('name')
      propertyList.append(prop)
    
  def get_profiles(self, profileList, accountId, propertyId):
    profiles = self.service.management().profiles().list(
      accountId=accountId,
      webPropertyId=propertyId)
    http = self.decorator.http()
    response = profiles.execute(http=http)
    for item in response.get('items'):
      profile = dict()
      profile['id'] = item.get('id')
      profile['name'] = item.get('name')
      profileList.append(profile)
    
  def get_segments(self, segmentList):
    segments = self.service.management().segments().list()
    http = self.decorator.http()
    response = segments.execute(http=http)
    for item in response.get('items'):
      segment = dict()
      segment['id'] = item.get('id')
      segment['name'] = item.get('name')
      segmentList.append(segment)
    
  def get_metrics(self,profileId,startDate,endDate,metrics,segmentId):
    results = self.service.data().ga().get(
      ids='ga:' + profileId,
      start_date=startDate,
      end_date=endDate,
      metrics=metrics)
    http = self.decorator.http()
    response = results.execute(http=http)
    return response

class DoubleClick(object): 

  def __init__(self, decorator):
    self.service = build('dfareporting', 'v1.1')
    self.decorator = decorator

  def get_profiles(self, profileList):
    profiles = self.service.userProfiles().list()
    http = self.decorator.http()
    response = profiles.execute(http=http)
    for item in response.get('items'):
      profile = dict()
      profile['profileId'] = item.get('profileId')
      profile['accountId'] = item.get('accountId')
      profileList.append(profile)

  def get_reportList(self, profileId, reportList): 
    reports = self.service.reports().list(profileId=profileId)
    http = self.decorator.http()
    response = reports.execute(http=http)
    for item in response.get('items'):
      report = dict()
      report['id'] = item.get('id')
      reportList.append(report)
    
  def get_fileList(self, profileId, reportId, files): 
    reports = self.service.reports().files().list(profileId=profileId,
      reportId=reportId)
    http = self.decorator.http()
    response = reports.execute(http=http)
    for item in response.get('items'):
      f = dict()
      f['id'] = item.get('id')
      files.append(f)
    
  def get_file(self, profileId, reportId, fileId, fileObj): 
    reports = self.service.reports().files().get(profileId=profileId, 
      reportId=reportId,
      fileId=fileId)
    http = self.decorator.http()
    response = reports.execute(http=http)
    fileObj['id'] = response.get('id')
    fileObj['reportId'] = response.get('reportId')
    fileObj['apiUrl'] = response.get('urls').get('apiUrl')
    
  def get_metrics(self, profileId, startDate, endDate, dimensionName): 
    body = dict()
    body['kind'] = 'dfareporting#dimensionValueRequest'
    body['dimensionName'] = 'dfa:' + dimensionName
    body['startDate'] = startDate
    body['endDate'] = endDate
    body['filters'] = list()
    results = self.service.dimensionValues().query(profileId=profileId,
      body=body)
    http = self.decorator.http()
    response = results.execute(http=http)
    return response
