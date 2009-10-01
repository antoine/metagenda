import traceback,sys
import urllib2
import utils
import re
from datetime import datetime
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup
#default_encoding2 = 'windows-1252'
daysAbbr={
        'Mon':1,
        'Tue':2,
        'Wed':3,
        'Thu':4,
        'Fri':5,
        'Sat':6,
        'Sun':7}

reverseMonthsAbbr={
        'Jan':1,
        'Feb':2,
        'Mar':3,
        'Apr':4,
        'May':5,
        'Jun':6,
        'Jul':7,
        'Aug':8,
        'Sep':9,
        'Oct':10,
        'Nov':11,
        'Dec':12}

reverseMonths={
        'January':1,
        'February':2,
        'March':3,
        'April':4,
        'May':5,
        'June':6,
        'July':7,
        'August':8,
        'September':9,
        'October':10,
        'November':11,
        'December':12}
DEFAULT_YEAR = datetime.now().year

NOT_FREE = 0
FREE = 1
MAYBE_FREE = 2

free_re = re.compile('(.*free.*)|(.*gratuit.*)|(.*vrij.*)|(.*gratis.*)', re.I | re.DOTALL)
maybe_not_free_re = re.compile('(.*lady.*)|(.*ladies.*)|(.*girl.*)|(.*before.*)|(.*b4.*)|(.*voor.*)|(.*avant.*)|(.*fille.*)', re.I | re.DOTALL)
class Event:
    def __init__(self, name=None, place=None, time=None, source=None, url=None, info=None, style=None, is_free= 0):
        self.name = name
        self.place = place
        self.time = time
        self.url = url
        self.source = source
        self.info= info
        self.style=style 
        #is_free can have 3 values depending what kind of info we gather : no, yes, maybe ;)
        self.is_free = is_free

    def __str2__(self):
       return "[%s - %s - %s - %s - %s - %s - %s - %s]" % utils.encode_as_tuple(
                [self.name, self.place, self.time, self.info, self.style, self.source, self.url, self.is_free])

    def as_tuple(self):
        return tuple([utils.capitalize_words(self.name), self.place, self.time, self.source, self.url, self.info, self.style, self.is_free])
    def encode(self):
        self.name = utils.encode_null(self.name)
        self.place = utils.encode_null(self.place)
        self.url = utils.encode_null(self.url)
        self.source = utils.encode_null(self.source)
        self.info= utils.encode_null(self.info)
        self.style= utils.encode_null(self.style)



def remove_nbsp(data):
    return data.replace(u'\xa0', '')
def remove_e(data):
    return data.replace(u'\u20ac', 'E')

def parse_ab():
    remotepage = 'http://www.abconcerts.be/concerts/concertlijst.html'
    baseurl = 'http://www.abconcerts.be/concerts/'
    localpage = "file:///D:/home/hacking/hg/hacking/webpy/glocal/data/ab.html"
    page = urllib2.urlopen(remotepage)
    soup = BeautifulSoup(page, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
    tables = soup.findAll('table')
    dateFinder = re.compile('[0-9]+')

    events = []
    source = 'ab'

    ##ok so the fourth table contains all data for the concerts.
    for line in tables[4].findAll(name='tr'):
        eventData = line.findAll(name='td')

        #sometimes the AB add empty lines at the end of the table
        if len(eventData)>1  and eventData[0].find('font'):
            e = Event(source=source);
            dateData = dateFinder.findall(eventData[0].find('font').string)
            e.time = datetime(int(dateData[2]), int(dateData[1]), int(dateData[0]), 22)
            artistData = eventData[1].findAll('a')
            e.url = baseurl + artistData[len(artistData)-1]['href']
            e.name = remove_nbsp(artistData[len(artistData)-1].string.replace('&nbsp;', ''))
            e.place = eventData[2].find('font').string
            events.append(e)

    return events


def parse_boups():
    remotepage = 'http://www.boups.com/agenda/simple'
    localpage = "file:///D:/home/hacking/hg/hacking/webpy/glocal/data/boupssimple.htm"
    source = 'boups'
    page = urllib2.urlopen(remotepage)
    soup = BeautifulSoup(page, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
    eventsData = soup.findAll('li')
    events = []
    for event in eventsData:
        e = Event(source=source)
        e.name = event.find('span', 'partyname').string.strip()
        e.style = event.find('span', 'genres').string.strip()
        if event.find('span', 'partyurl'):
            e.url = event.find('span', 'partyurl').string.strip()
        if event.find('span', 'price free'):
            e.is_free = FREE
            e.info = event.find('span', 'price free').string.strip()
        else:
            e.info = event.find('span', 'price').string.strip()

        e.info = remove_e(e.info) 
            
        dateData = event.find('span', 'when').string.strip().split('-')
        e.time = datetime(int(dateData[2]), int(dateData[1]), int(dateData[0]), 22)
        e.place = event.find('span', 'wherename').string.strip()
        if not event.find('span', 'cancelled'):
            events.append(e)
    return events


def parse_kvs():
    
    remotepage = 'http://www.kvs.be/index2.php?page=program&discipline=5&lng=ENG'
    localpage = ""
    place = "KVS"
    defaultYear = str(DEFAULT_YEAR)
    page = urllib2.urlopen(remotepage)
    soup = BeautifulSoup(page, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
    tables = soup.findAll('table', attrs={'width':'570'})
    source = 'kvs'
    events = []
    for table in tables[3:]:
        e = Event(source=source, place=place)
        e.name = table.find('div', 'titelgroen').string
        url = table.find(text=lambda a:  a.find('read more') >= 0)
        if url:
            e.url = url.parent['href']

        dateData = table.find('table').find('div').string.strip().replace('&nbsp;', ' ')
        if (dateData.find('from') >=0):
            dateSplit = dateData.split()
            parsedDate = [dateSplit[1], reverseMonthsAbbr[dateSplit[2]], defaultYear]
        else:
            dateSplit = dateData.split(',')[0].split()
            parsedDate = [dateSplit[0], reverseMonthsAbbr[dateSplit[1]], dateSplit[2]]
        e.time = datetime(int(parsedDate[2]), int(parsedDate[1]), int(parsedDate[0]), 22)
        events.append(e)

    return events

def parse_noctis():
    remotepages = ['http://noctis.com/pages/events/agenda.php', 
            'http://noctis.com/pages/events/agenda.php?decallage_=7',
            'http://noctis.com/pages/events/agenda.php?decallage_=14',
            'http://noctis.com/pages/events/agenda.php?decallage_=21',
            'http://noctis.com/pages/events/agenda.php?decallage_=28']
    localpage = ""
    source = 'noctis'
    events = []
    for remotepage in remotepages:
        page = urllib2.urlopen(remotepage)
        soup = BeautifulSoup(page, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
        dayTables = soup.findAll('table', attrs={'name' : 'jour'})
        year = DEFAULT_YEAR 
        for table in dayTables:
            dateData = table.find('span', id='tdays').string.split(' ')
            time = datetime(year, int(reverseMonths[dateData[2]]),int(dateData[1]), 22)
            parties = table.findAll('span', id='agenda2');
            for party in parties:
                e = Event(source=source, time=time)
                sep = party.findNextSibling(name='span', id='agendat').findAll('br')
                place = sep[len(sep)-2].findNextSibling(text = lambda(text): len(text) > 1)
                e.name = party.contents[0].split('@')[0]
                e.place = place.replace('@', '').strip()
                info = sep[len(sep)-3].findNextSibling(text = lambda(text): len(text) > 1)
                e.info = info.replace('*', '').strip()
                e.style = party.findPrevious('span', id='agstyle').find(text= lambda(text): len(text) > 1).strip().replace('::', '')
                url = party.findNextSibling('span', id='agendau')
                if url:
                    e.url = url.find('a')['href']
                #we check if free is in the name
                e.info = remove_e(e.info) 
                e.is_free = is_free(e.name, e.info)
                events.append(e)
    return events

def is_free(partyname, partyinfo):
    if free_re.match(partyname):
        return FREE 
    else:
        #if not then maybe we can find it in the infos, but if the infos have mention of lady/ladies and other stuff it might only be free for them
        if free_re.match(partyinfo):
            if maybe_not_free_re and maybe_not_free_re.match(partyinfo):
                return MAYBE_FREE
            return FREE 
        return NOT_FREE


def parse_recyclart():
    remotepage = 'http://www.recyclart.be/content/blogcategory/93/14/lang,en/'
    localpage = ""
    page = urllib2.urlopen(remotepage)
    soup = BeautifulSoup(page, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
    source = 'recyclart'
    place = 'recyclart'
    eventsData = soup.findAll('li', 'Musique')
    events = []
    for event in eventsData:
        e = Event()
        e.name = event.find('h1').string.strip()
        e.url = event.find('div', 'visual').first()['href'].replace('lang,en', 'lang,fr')
        dateData =  event.find('div', 'date').findAll(text = lambda(text): len(text) > 1)[1].string
        dateSplit = dateData.split('-')[0].split()
        #TODO: extract price/info 
        e.time = datetime(int(dateSplit[3]), int(reverseMonths[dateSplit[2]]), int(dateSplit[1]), 22)
        e.place = place
        e.source = source
        events.append(e)
    return events

def parse_brusselssucks():
    remotepage = 'http://partyinbrussels.googlepages.com/brusselssucks'
    localpage = ""
    page = urllib2.urlopen(remotepage)
    soup = BeautifulSoup(page, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
    source = 'brusselssucks'
    year = DEFAULT_YEAR 
    eventsData = soup.findAll('h4')
    events = []
    for event in eventsData:
        try:
            e = Event()
            e.source = source
            time_price_place = event.string.split('@')
            e.place = time_price_place[1]

            name = event.nextSibling
            if name.string:
                e.name = name.string
            else:
                #url needs to be parsed, is it website bound
                e.url = name.first()['href']
                e.name = name.first().string

            time_price = time_price_place[0].split(',')
            if len(time_price) >= 3:
                e.info = time_price[2]
                e.info = remove_e(e.info) 
                e.is_free = is_free(e.name, e.info)
            time = time_price[0].split()
            e.time = parse_brusselssucks_date(time,year)
            
            events.append(e)
        except Exception, e:
            traceback.print_exc(file=sys.stdout)
            print "could not parse :\n%s" % (event.prettify())
    return events

def parse_brusselssucks_date(datedata, default_year):
    index_offset = 0
    #we assume the month is first
    if (reverseMonthsAbbr.has_key(datedata[1])):
        #if we find a month in second, then the date must be third
        index_offset = 1
    return datetime(default_year, reverseMonthsAbbr[datedata[index_offset]], int(datedata[1+index_offset]), 22)

if __name__ == "__main__": 
    events = parse_boups()
#    events.extend(parse_noctis())
#    events.extend(parse_ab())
#    events.extend(parse_recyclart())
    for e in events:
        print ',("""%s""", """%s""", """%s""", """%s""")' % (e.name.encode('utf-8'), e.place.encode('utf-8'), e.time, e.source)
