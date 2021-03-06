#!/usr/bin/env python

import sys
import datetime
import logging
import json
import csv
import os.path

import optparse
import ConfigParser
import flickrapi

if __name__ == '__main__' :

    parser = optparse.OptionParser()
    parser.add_option("-c", "--config", dest="config", help="path to an ini config file")
    parser.add_option("-u", "--user-id", dest="user_id", help="the user to fetch photos for")
    parser.add_option("-o", "--outdir", dest="outdir", help="where to write data files")
    parser.add_option('-v', '--verbose', dest='verbose', action='store_true', default=False, help='be chatty (default is false)')

    (opts, args) = parser.parse_args()

    if opts.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)


    cfg = ConfigParser.ConfigParser()
    cfg.read(opts.config)

    api_key=cfg.get('flickr', 'api_key')
    api_secret=cfg.get('flickr', 'api_secret')

    flickr = flickrapi.FlickrAPI(api_key, api_secret)
    (token, frob) = flickr.get_token_part_one(perms='read')
    if not token: raw_input("Press ENTER after you authorized this program")
    flickr.get_token_part_two((token, frob))

    # sudo put me in a library or something...
    # (20130930/straup)

    if opts.user_id == 'me':
        data = flickr.auth_checkToken()
        opts.user_id = data.find('auth').find('user').attrib['nsid']

    current_year = None
    writer = None

    for ph in flickr.walk(
        user_id = opts.user_id,
        extras = 'date_taken,date_upload,owner_name,geo,date_taken,url_m,url_n,url_c,url_l',
        sort = 'date-posted-asc'):

        dt = ph.attrib['datetaken']
        dt = dt.split('-')
        year_taken = dt[0]

        ymd = ph.attrib['datetaken'].split(' ')
        ymd = ymd[0]
        
        title = ph.attrib['title']
        owner = ph.attrib['ownername']
        
        full_img = None

        for url in ('url_l', 'url_c', 'url_m'):

            if ph.get(url):
                full_img = ph.attrib[url]
                break

        logging.debug("full_img is %s" % full_img)

        photo_page = "http://www.flickr.com/photos/%s/%s" % (ph.attrib['owner'], ph.attrib['id'])

        desc = ""

        if title != '':
            desc = "%s (%s)" % (title, ymd)
        else:
            desc = "(%s)" % ymd

        meta = json.dumps({
                'og:description': desc,
                'pinterestapp:source': photo_page,
                })

        row = {
            'full_img': full_img,
            'id': ph.attrib['id'],
            'meta': meta,
            }

        logging.debug(row)

        if not current_year or year_taken != current_year:

            current_year = year_taken
            fname = "flickr-photos-%s.csv" % current_year

            path = os.path.join(opts.outdir, fname)

        if os.path.exists(path):

            logging.debug("append row to %s" % path)

            fh = open(path, 'a')
            writer = csv.DictWriter(fh, fieldnames=('full_img', 'id', 'meta'))

        else:

            logging.debug("write row %s" % path)

            fh = open(path, 'w')

            writer = csv.DictWriter(fh, fieldnames=('full_img', 'id', 'meta'))
            writer.writeheader()

        writer.writerow(row)

    logging.info("done")
    sys.exit()
