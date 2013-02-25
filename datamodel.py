
## google OAuth 2.0 and API imports
from oauth2client.appengine import CredentialsProperty
from oauth2client.appengine import StorageByKeyName

## standard python library imports
from datetime import datetime
import logging

## from utility import *
from google.appengine.ext import db

class CredentialsModel(db.Model):

  credentials = CredentialsProperty()
  added = DateTimeProperty(auto_now_add=True)

  @classmethod
  def __storeCredentials(self, userid, propName):
    storage = StorageByKeyName(CredentialsModel, userid, propName)
    credentials = storage.get()
    storage.put(credentials)
