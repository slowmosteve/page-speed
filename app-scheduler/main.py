import webapp2
import urllib2
import os
from google.appengine.api import urlfetch

class CronJob(webapp2.RequestHandler):
    def get(self):
        # increase url fetch timeout
        urlfetch.set_default_fetch_deadline(600)
        request = urllib2.Request("REPLACE WITH GCF URL", headers={"cronrequest" : "true"})
        contents = urllib2.urlopen(request).read()

page_speed = webapp2.WSGIApplication([
    ('/page_speed', CronJob),
    ], debug=True)