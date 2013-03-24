Ad Dash
==============

Purpose:
--------------
*Ad Dash* was designed to query Google Analytics and DoubleClick Floodlight OLAP systems. A user who authenticates with a google account with access to GA or DFA reporting will be able to query GA and/or DFA for basic metrics and reports.  

Components:
--------------
 * Google App Engine 1.7.5
 * App Engine DataStore
 * Python 2.7
 * webapp2 (restful wsgi framework)
 * jinja2 (templates)
 * OAuth 2.0
 * Google Analytics Core Reporting API
 * DoubleClick Floodlight Reporting API

Features:
--------------
 * Google Analytics Query Tool for fetching and displaying up to 10 metrics at one time for a specific time period.
    * metrics can be sliced using advanced segments
 * DoubleClick Floodlight query Tool for fetching and displaying DFA report metrics (still under development)
