"""Controlbot management pages."""

from contextlib import closing

import datetime
import json
import logging
import time

from google.appengine.api import memcache
from google.appengine.ext import db

from base_page import BasePage
from pytz.gae import pytz
import utils


CONFIG_MEMCACHE_KEY = 'controlbot_config'

LOCAL_TZ = pytz.timezone('US/Eastern')


class ControlbotConfig(db.Model):
  """Description for the config table. It will be a singleton for simplicity."""
  # Whether the controlbot is running or not.
  last_reported = db.DateTimeProperty()
  should_stop = db.BooleanProperty()
  target_temperature = db.FloatProperty()
  room_temperature = db.FloatProperty()
  # TODO(ravi): Add ability to do view and edit schedules.
  schedules = db.TextProperty()


def _get_config():
  config = memcache.get(CONFIG_MEMCACHE_KEY)
  if config == None:
    config = db.Query(ControlbotConfig).get()
    memcache.add(CONFIG_MEMCACHE_KEY, config)
  return config


def _flush_cache():
  memcache.flush_all()
  memcache.delete(CONFIG_MEMCACHE_KEY)
  time.sleep(1)


class MainPage(BasePage):

  @utils.require_user
  @utils.admin_only
  def post(self):
    config = _get_config()
    config.should_stop = bool(self.request.get('should_stop'))
    config.put()
    _flush_cache()
    self._handle(config)

  @utils.require_user
  @utils.admin_only
  def get(self):
    config = _get_config()
    self._handle(config)

  def _handle(self, config):
    template_values = self.InitializeTemplate('Nest Controlbot Page')
    template_values['config'] = config
    time_diff = datetime.datetime.now() - config.last_reported
    template_values['mins_ago'] = time_diff.seconds/60
    template_values['last_reported'] = config.last_reported.replace(
        tzinfo=pytz.utc).astimezone(LOCAL_TZ)
    self.DisplayTemplate('main.html', template_values)


class GetStatusPage(BasePage):
  def get(self):
    config = _get_config()
    json_dict = {
        'stop': config.should_stop,
    }
    json_output = json.dumps(json_dict)
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(json_output)


class UpdateStatusPage(BasePage):
  @utils.admin_only
  def post(self):
    # Read values.
    target_temperature = float(self.request.get('target_temperature'))
    room_temperature = float(self.request.get('room_temperature'))
    # Set it to the config.
    config = _get_config()
    config.target_temperature = target_temperature
    config.room_temperature = room_temperature
    config.last_reported = datetime.datetime.now()
    config.put()
    # Flush the cache.
    _flush_cache()


def bootstrap():
  # Guarantee that at least one instance exists.
  if db.GqlQuery('SELECT __key__ FROM ControlbotConfig').get() is None:
    ControlbotConfig(
        last_reported=datetime.datetime.now(),
        should_stop=False,
        schedules="{}",
        target_temperature=72.0,
        room_temperature=71.0).put()

