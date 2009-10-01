#!/usr/bin/env python2.4
import config
import web
from view import render
import parsers, db

urls = (
        '/', 'index',
        '/admin', 'admin',
        '/admin/locations/(\w+)', 'location_management',
        '/admin/event/(\d+)', 'event_admin',
        '/feed\.(\w+)', 'feed',
        '/from/(\w+)/feed\.(\w+)', 'source',
        '/from/(\w+)', 'source',
        '/event/daymap/([-\w]+)', 'daymap',
        '/event/(\w+)', 'event'
        )

class index:
    def GET(self):
        events = db.get_events(order='time_start, name',  where='not cancelled and duplicateof is null and time_start >= date_sub(current_timestamp, interval 5 hour)')
        web.debug(len(events))
        print render.base(render.show_events( events, admin=False))

class admin:
    def GET(self):
        events = db.get_events( order='time_start, name', \
                where='not cancelled and time_start >= date_sub(current_timestamp, interval 5 hour)')
        web.debug(len(events))
        print render.base(render.show_events( events, admin=True))

class location_management:
    def GET(self, comparison_name):
        """show a form to create a location"""
        if comparison_name == 'nomap':
            #showing a list of all locations withour a map
            events = web.select(tables='events', what='*', group='place', order='time_start', where='not cancelled and duplicateof is null and id_location is null' )
            print render.base(render.show_locations( events))
        elif comparison_name:
            #updating a specific location
            location = [l for l in web.select(tables='locations', where="comparison_name = '%s'" % comparison_name)]
            if len(location):
                print render.base(render.manage_location(location[0].longitude,location[0].latitude, location[0].originalmapurl, location[0].id, comparison_name))
            else:
                print render.base(render.manage_location(None, None, None, None, comparison_name))
        else:
            print "not implemented yet"

    def POST(self, comparison_name):
        """create or update a location data"""
        i = web.input()
        if i.gmapurl:
            #gmap urls sometime contains a sll parameter
            finder = '&ll='
            if i.gmapurl.find(finder) == -1:
                finder = '?ll='
                if i.gmapurl.find(finder) == -1:
                    print('could not find ll parameter in map url')
                    #interrupting execution
                    return
            web.debug(i.gmapurl)
            web.debug(finder)
            web.debug(i.gmapurl.find(finder))
            if finder:
                ll = i.gmapurl[i.gmapurl.find(finder)+4:i.gmapurl.find('&', i.gmapurl.find(finder)+1)].split(',')
                longitude = ll[0]
                latitude = ll[1] 
                mapurl = i.gmapurl
        else:
            longitude = i.longitude
            latitude = i.latitude
            mapurl = None

        if i.location_id:
            #updating/replacing
            web.query("update locations set longitude = %s, latitude = %s, originalmapurl = '%s' where id = %s" % (longitude, latitude, mapurl, i.location_id))
        else:
            #creating
            location_id= web.insert('locations', comparison_name=comparison_name, longitude=longitude, latitude=latitude, originalmapurl=mapurl)
            if not location_id:
                raise Exception('Error when creating location for '% comparison_name)
            db.add_new_location(location_id, comparison_name)

        web.seeother('/admin/locations/nomap')

class daymap:
    def GET(self, date):
        datedata = date.split('-')
        if len(datedata) == 3:
            events = [e for e in db.get_events(order='name', where='not cancelled and duplicateof is null and year(time_start) = %s and month(time_start) = %s and dayofmonth(time_start) = %s' % tuple(date.split('-')))]
            web.debug(len(events))
            print render.daymap(events, date, render.show_events(events, admin=False, formap=True))
        else:
            web.debug("accessing the daymap with parameters %s" % date)
            web.seeother('/')

class event:
    def GET(self, event_id):
        print "not implemented yet"

class event_admin:
    def POST(self, event_id):
        web.debug("updating event")
        i = web.input()
        if i.action == 'undo':
            web.debug("un-marking event as duplicateof")
            web.query("update events set duplicateof = null where id = %s" % (event_id))
        elif i.action == 'mark':
            if i.duplicateof != event_id:
                web.debug( "marking event as duplicate of %s" % i.duplicateof)
                web.query("update events set duplicateof = %s where id = %s" % (i.duplicateof, event_id))
            else:
                web.debug("trying to mark an event as a duplicate of itself: %s" % i.duplicateof)
                
        else:
            web.debug("nothing to do")
        web.seeother('/admin')

class source:
    def GET(self, source, feed_type=None):
        if not feed_type:
            events = db.get_events(order='time_start, name',  
                where="not cancelled and time_start >= date_sub(current_timestamp, interval 5 hour) and taken_from= '%s'" % (source))
            web.debug(len(events))
            #add source specific feed
            print render.base(render.show_events( events, admin=False), feeds=["""
                <link rel="alternate"
                type="application/atom+xml" title="%s calendar - Atom"
                href="http://%s/from/%s/feed.atom" />
            """ % (source, config.server_root_url, source),])
        else:
            events = [e for e in db.get_events(limit='100', order='time_taken desc', where ="taken_from= '%s'" % (source))]
            render_cached_feed(events, feed_type)

class feed:
    def GET(self, format_type='atom'):
        events = [e for e in db.get_events(limit='100', order='time_taken desc', where='duplicateof is null')]
        web.debug(type(events[0].name))
        render_cached_feed(events, format_type)

def render_cached_feed(events, format_type='atom'):
    last_modif_time = events[0].time_taken
    web.debug(last_modif_time)
    #http conditional get
    if not config.http_conditional_get or web.modified(last_modif_time):
        web.lastmodified(last_modif_time)
        web.header("Content-Type", "application/atom+xml")
        web.debug(len(events))
        print render.events_atom_feed(config, last_modif_time, events)


def runfcgi_apache(func):
    web.wsgi.runfcgi(func, None)

if __name__ == "__main__": 
    import os
    if "LOCAL" not in os.environ:
        #web.wsgi.runwsgi = runfcgi_apache
        pass
    web.run(urls, globals(), *config.middleware)
    #application = web.wsgifunc(web.webpyfunc(urls, globals()))
