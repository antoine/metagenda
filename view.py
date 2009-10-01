#!/usr/bin/env python2.4
# -*- coding: iso-8859-1 -*-
import web, parsers, utils
from datetime import datetime, timedelta
import config
import re


render = web.template.render('templates/', cache=config.cache)

def render_relative_time(time):
    now = datetime.now()
    tonight = now -timedelta(hours=7) 
    tomorrow = now + timedelta(hours=17) 
    
    if now.isoweekday() > 4:
        #we are the we the next friday is in at least 6 days
        next_friday = now + timedelta(days=(7 - now.isoweekday())+5)
        we_prefix = 'next'
    else:
        next_friday = now + timedelta(days=5 - now.isoweekday())
        we_prefix = 'coming'


    if date_equals(time, tonight):
        return '<span class="when">tonight</span>'
    elif date_equals(time, tomorrow):
        return '<span class="when">tomorrow</span>'
    elif date_equals_we(time, next_friday):
        return '<span class="when">%s we</span>'% (we_prefix)
    else:
        return ''

def render_time(time, header=False):
    now = datetime.now()

    day_format = '%A %d'
    hour_suffix = ', %Hh'
    month_format = ' %b'
    if header:
        day_format = ' <span class="wkday">%A</span> <span class="numba">%d</span>'
        month_format = ' <span class="month">%B</span>'
        hour_suffix = ''

    if time.year != now.year:
        return time.strftime(day_format + month_format+' %Y' + hour_suffix)
    else:
        return time.strftime(day_format + month_format + hour_suffix)

def to_utf8(data):
    if isinstance(data, str):
        return data.decode('iso-8859-1').encode('utf-8')
    else:
        return data

def to_utf8_entity(data):
    if isinstance(data, str):
        return web.htmlquote(data).decode('iso-8859-1').encode('ascii', 'xmlcharrefreplace')
    else:
        return web.htmlquote(data)

def render_microformat_time(time):
    return time.strftime('%Y%m%dT%H00')

def render_microformat_time_end(time):
    return (time + timedelta(hours=5)).strftime('%Y%m%dT%H00')

def date_equals(date1, date2):
    return date1.day == date2.day and date1.month == date2.month and date1.year == date2.year

def date_equals_we(date1, we_friday):
    return date_equals(date1, we_friday) or (date_equals(date1, we_friday+ timedelta(days=1))) or (date_equals(date1, we_friday+ timedelta(days=2)))

def get_config(propname):
    return getattr(config, propname)

def render_date(time):
    return time.strftime('%Y%m%d')

def render_feed_time(time):
    return time.strftime('%A %d %b, %Hh')

def render_rfc3339_time(tentry):
    _format_RFC3339 = "%Y-%m-%dT%H:%M:%SZ"
    if tentry is None:
        return ""

    return (tentry - timedelta(hours=2)).strftime(_format_RFC3339)

def render_gmap_link(e):
    if e.mapurl:
        return e.mapurl
    else:
        return "http://maps.google.com/maps?q=%s,%s" % (e.longitude,e.latitude)

def render_gmap_bubble_text(e):
    return ("%s<br><a href='%s'>view in google maps</a>" %(e.name, render_gmap_link(e))).replace("'", "\\'")

web.template.Template.globals.update(dict(
  datestr = web.datestr,
  len = len,
  type = type,
  compress = utils.remove_uneeded,
  to_utf8= to_utf8,
  to_utf8_entity= to_utf8_entity,
  render_time = render_time,
  render_relative_time= render_relative_time,
  render_microformat_time= render_microformat_time,
  render_microformat_time_end= render_microformat_time_end,
  render_rfc3339_time= render_rfc3339_time,
  render_feed_time= render_feed_time,
  render_date= render_date,
  render_gmap_link= render_gmap_link,
  render_gmap_bubble_text= render_gmap_bubble_text,
  get_config = get_config,
  render = render
))
