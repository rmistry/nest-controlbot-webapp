"""AppEngine scripts to manage the nest-controlbot webapp."""

from google.appengine.ext import webapp

import base_page
import controlbot
import utils


class Warmup(webapp.RequestHandler):
  def get(self):
    """This handler is called as the initial request to 'warmup' the process."""
    pass


# Application configuration.
URLS = [
  ('/', controlbot.MainPage),
  ('/get_status?', controlbot.GetStatusPage),
  ('/update_status?', controlbot.UpdateStatusPage),
]
APPLICATION = webapp.WSGIApplication(URLS, debug=True)


# Do some one-time initializations.
base_page.bootstrap()
controlbot.bootstrap()
utils.bootstrap()
