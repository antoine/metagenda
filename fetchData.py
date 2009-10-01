#!/usr/bin/env python2.4
# -*- coding: UTF-8 -*-
import editdist
import MySQLdb
import parsers, db, config, utils
import re
from datetime import datetime, timedelta

def check_replacing(party, possible_dead_events):
    possible_dead = []
    possible_match = 0 
    for pde in possible_dead_events:
        #we allow for a slight change in name when updating the place 
        if party.time == pde[3] and utils.same(party.place, pde[2]) and utils.same(party.name, pde[1]):
            possible_match = pde[0] 
        else:
            possible_dead.append(pde)
    return (possible_match, possible_dead) 

def check_redating(party, possible_dead_events):
    possible_dead = []
    possible_match = 0 
    for pde in possible_dead_events:
        #we allow for a slight change in name when updating the date
        if party.time != pde[3] and utils.same(party.place, pde[2]) and utils.same(party.name, pde[1]):
            possible_match = pde[0] 
        else:
            possible_dead.append(pde)
    return (possible_match, possible_dead) 

def check_renaming(party, possible_dead_events):
    possible_dead = []
    possible_match = 0 
    for pde in possible_dead_events:
        #date is 2 for www, 3 for pde
        #place is 1 for www, 2 for pde
        #name is 0 for www, 1 for pde
        if party.time == pde[3] and utils.same(party.name, pde[1]):
            possible_match = pde[0] 
        else:
            possible_dead.append(pde)
    return (possible_match, possible_dead) 


def main():
    print "\n\n----------------------------"
    print datetime.now()
    sources = ['ab', 'boups', 'kvs', 'recyclart', 'brusselssucks']
    events = []
    unreacheable_sources = []
    for source in sources:
        print "parsing source %s" % source
        try:
            events.extend(getattr(parsers, "parse_%s" % source)())
        except Exception, e:
            print "## could not read %s because : %s" % (source, str(e))
            unreacheable_sources.append(source)


    
    print "%s events fetched from www" % len(events)

    db_config = config.db_parameters
    db_config.pop('dbn')
    db = MySQLdb.connect(**db_config)
    cursor = db.cursor()
    cursor.execute("set names utf8;")
    cursor.execute(" show variables like 'colla%'")
    print(cursor.fetchall())

    #we will have lots of identical events, a few updated events, and a few new events.
    #between 200-400 events are present at all time, they can all fit in a structure for comparison
    new_events = []
    old_events_ids = []
    for e in events:
        e.encode()
        cursor.execute( "select id from events where time_start = %s and name = %s and place = %s and not finished", (e.time, e.name, e.place));
        data = cursor.fetchone()
        if data:
            #print "this party already exists: %s %s" % (e[0], e[2])
            #[0] since we have one result with one field 
            old_events_ids.append(str(data[0]))
        else:
            new_events.append(e)
    print "\n%s old parties found." % len(old_events_ids)
    print "%s new parties found\n" % len(new_events)
    if old_events_ids:
        #check which parties are not listed anymore
        if unreacheable_sources:
            cursor.execute("select id, name, place, time_start, taken_from from events where id not in (%s) and not (cancelled or finished) and taken_from not in ('%s')" % (','.join(old_events_ids), "','".join(unreacheable_sources)))
        else:
            cursor.execute("select id, name, place, time_start, taken_from from events where id not in (%s) and not (cancelled or finished)" % (','.join(old_events_ids)))
        possible_dead_db_events = cursor.fetchall()
        #a party can be dead if it's not listed anymore or if the name changed, or if it was cancelled.
        #those parties are too old in the DB

        print "\n- old parties from DB: " 
        for par in [p for p in possible_dead_db_events if p[3] < (datetime.now() - timedelta(hours=5))]:
            print "  - %s" % str(par)
            print ("update events set finished = true where id = %s"% (par[0]))
            cursor.execute("update events set finished = true where id = %s", (par[0]))
        really_new_events= []

        print "\n- updated parties: " 
        for p in new_events:
            #we check for renaming, redating and replacing, if more than one changed then the party will be cancelled and recreated instead of just updated
            (possible_match, possible_dead_db_events) = check_renaming(p, possible_dead_db_events)
            if not possible_match:
                (possible_match, possible_dead_db_events) = check_redating(p, possible_dead_db_events)
                if not possible_match:
                    (possible_match, possible_dead_db_events) = check_replacing(p, possible_dead_db_events)
            if possible_match:
                print p.name.__repr__()
                print "  - %s %s possibly match with party %s" % (p.time, utils.encode_null(p.name), possible_match)
                print ("update events set name =%s, place= %s, time_start = %s, updated = %s where id = %s"% (utils.capitalize_words(p.name), p.place, p.time, datetime.now(), possible_match))
                cursor.execute("update events set name =%s, place= %s, time_start = %s, updated = %s where id = %s", (utils.capitalize_words(p.name), p.place, p.time, datetime.now(), possible_match))
                set_location(cursor, possible_match, p.place)
            else:
                really_new_events.append(p)

        print "\n- cancelled parties:" 
        for par in [p for p in possible_dead_db_events if p[3] >= datetime.now()]:
            print "  - %s" % str(par)
            print ("update events set cancelled = true, updated = %s where id = %s"% (datetime.now(), par[0]))
            cursor.execute("update events set cancelled = true, updated = %s where id = %s", (datetime.now(), par[0]))
        new_events = really_new_events


    print "\n- new parties : "
    #new parties have to be checked for possible cross reference across different sources
    #levenstheim distance has to be computed in order to check for different spellings

    for e in new_events:

        print "- %s" % e.__str2__()
        cursor.execute("select id, name, place, time_start, taken_from from events where time_start = %s", (e.time))
        parties_of_the_day = cursor.fetchall()
        has_twin = False
        #we have to check that the party was not alreade entered by another source, and we have to allow for some variation in the naming
        for potd in parties_of_the_day:
            #is same place and date we allow for greater variation
            #ok si if 2 parties have the same name but a different adress on the same night one gets ignored, too bad.
            if (utils.same(potd[1], e.name, 0.2)  and utils.same(potd[2], e.place, 0.6)) or (utils.same(potd[1], e.name, 0.6)  and utils.same(potd[2], e.place, 0.2)):

                #identical party
                print "## found identical event: \n\t%s %s %s %s, %s\n\t%s %s %s %s" % (potd[1], potd[2], potd[3], potd[4], potd[0], utils.encode_null(e.name), utils.encode_null(e.place), e.time, e.source)
                print ("insert into events (name, place, time_start, taken_from, duplicateof) values (%s, %s, %s, %s, %s)" % utils.encode_as_tuple([utils.capitalize_words(e.name), e.place, e.time, e.source, potd[0]]))
                insertargs = list(e.as_tuple())
                insertargs.append(potd[0])

                cursor.execute("insert into events (name, place, time_start, taken_from, url, info, style, is_free, duplicateof) values (%s, %s, %s, %s, %s, %s, %s, %s, %s)" , tuple(insertargs))
                has_twin = True
                break
        if not has_twin:
            print ("insert into events (name, place, time_start, taken_from) values (%s, %s, %s, %s)" % utils.encode_as_tuple([utils.capitalize_words(e.name), e.place, e.time, e.source]))
            cursor.execute("insert into events (name, place, time_start, taken_from, url, info, style, is_free) values (%s, %s, %s, %s, %s, %s, %s, %s)" , e.as_tuple())
            set_location(cursor, get_last_insert_id(cursor), e.place)


        #cursor.executemany("insert into events (name, place, time_start, taken_from) values (%s, %s, %s, %s)", events)
    print "DONE"
    print "----------------------------"

    
def set_location(cursor, event_id, event_place):
    cursor.execute('select id, comparison_name from locations')
    locations = cursor.fetchall()
    for location in locations:
        if utils.same(utils.remove_uneeded(event_place), location[1], 0.2):
            print("adding new location to event %s" % event_id)
            cursor.execute("update events set id_location = %s where id = %s" % (location[0], event_id))

def get_last_insert_id(cursor):
    cursor.execute("SELECT last_insert_id()")
    return cursor.fetchone()[0]

if __name__ == "__main__": main()

