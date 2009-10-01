import web
import utils
from datetime import date, timedelta, datetime

def add_new_location(location_id, comparison_name):
    events = web.select(tables='events', what='id, place', where='id_location is null')
    for event in events:
        if utils.same(utils.remove_uneeded(event.place), comparison_name, 0.2):
            web.debug("adding new location to event %s" % event.id)
            web.query("update events set id_location = %s where id = %s" % (location_id, event.id))

def get_events(**params):
    if not params.has_key('tables'):
        params['tables'] = 'events left join locations on events.id_location = locations.id'
    if not params.has_key('what'):
        params['what'] = 'events.*, locations.longitude as longitude, locations.latitude as latitude, locations.originalmapurl as mapurl, locations.id as loc_id'
    return web.select(**params)

