#!/usr/bin/env python2.4
import editdist
import re

nodata = re.compile("[^\w]*")
default_encoding = 'utf-8'

def same(d1, d2, value_of_same=0.1):
    #dis = editdist.distance(d1.upper(), d2.upper().encode('utf-8')) 
    #editdistance can accept two str or two unicode but if mismatch it will convert using ascii which doesn't work
    #dis = editdist.distance(unicode_to_str(d1.upper()), unicode_to_str(d2.upper()) )
    dis = editdist.distance(unicode_to_str(remove_uneeded(d1.upper())), unicode_to_str(remove_uneeded(d2.upper())) )
    if len(d2)> len(d1):
        longest_len = len(d2)
    else:
        longest_len =len(d1)
    levensthein_to_len = (1.0 * dis)/ longest_len
    return levensthein_to_len < value_of_same

def unicode_to_str(data):
    if type(data) == unicode:
        return data.encode('utf-8')
    else:
        return(data)

def encode_null( data, codec=default_encoding):
    if data:
        try:
            return data.encode(codec)
        except:
            return data
    else:
        return ''

def encode_as_tuple(data, codec=default_encoding):
    return tuple([encode_null(d, codec) for d in data])


def capitalize_words(s):
    return ' '.join([w.capitalize() for w in s.split()])

def remove_uneeded(data):
    return nodata.sub('', data)
