import web, os


if "LOCAL" in os.environ:
    print "Running LOCAL"
    http_conditional_get = False
    server_root_url = "localhost:8080"
    cache = False 
    middleware = [web.reloader]
    db_parameters = \
        dict(host='localhost', dbn='mysql',user="user",passwd="",db="glocal")
        #dict(host='localhost', dbn='mysql',user="rouadec",passwd="Rouadec",db="antoine_agenda")
    googleAPIKey = 'ABQIAAAAN0vuD91lbFCiAN9IZ8hjqxQ4UWCHAN85m6fIg1kGvvlZDic9URQBiShpu0Rkon6t6VY5lsAz045QZw'



else:
    http_conditional_get = True 
    server_root_url = "metagenda.org"
    cache = False 
    middleware = []
    db_parameters = \
        dict(host='localhost', dbn='mysql',user="user",passwd="",db="antoine_agenda")
    googleAPIKey = 'ABQIAAAAN0vuD91lbFCiAN9IZ8hjqxRzkQYpdG_6LPwMItIGFeerYHC7hhTo9NCEd3LHoj0ffGYI1wIhyxyH5g'



web.config.db_parameters = db_parameters
sources = {
        'ab':{'favicon':'http://boups.com/img/metaagenda/absmall.gif', 'url':'http://www.abconcerts.be/'},
        'boups':{'favicon':'http://boups.com/img/favicon.ico', 'url':'http://boups.com'},
        'kvs':{'favicon':'http://www.kvs.be/design_elements/icon.ico', 'url':'http://www.kvs.be'},
        'noctis':{'favicon':'http://noctis.com/favicon.ico', 'url':'http://noctis.com'},
        'brusselssucks':{'favicon':'http://delaunay.org/bs.png', 'url':'http://www.brusselssucks.be/'},
        'recyclart':{'favicon':'http://www.recyclart.be/images/favicon.ico', 'url':'http://www.recyclart.be'}
       }
web.webapi.internalerror = web.debugerror
