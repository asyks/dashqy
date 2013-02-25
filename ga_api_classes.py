
## google OAuth 2.0 and API imports
from apiclient.discovery import build

## ga_service = build('analytics', 'v3')

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
    properties = self.service.management().webproperties().list(accountId=accountId)
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
    
  def get_results(self, profileId, start_date, end_date, metrics):
    results = self.service.data().ga().get(
      ids='ga:' + profileId,
      start_date='2012-06-01',
      end_date='2012-06-30',
      metrics='ga:visits')
    http = self.decorator.http()
    response = results.execute(http=http)
    return response
