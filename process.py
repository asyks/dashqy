#!/usr/bin/python
import logging

def process_ga_metrics(apiResponse):
  result = dict()
  response = apiResponse.get('totalsForAllResults')
  for k in response:
    value = response.get(k)
    rate , percent = k[-4:], k[3:10]
    if value.find('.'):
      value = round(float(value), 2)
    else:
      value = int(value)     
    if rate == 'Rate' or percent == 'percent':
      value = str(value) + '%'
    result[k] = value
  return result
