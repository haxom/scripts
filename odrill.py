#!/usr/bin/env python
#coding=utf8
__author__	= "haxom"
__email__	= "haxom@haxom.net"
__file__	= "odrill.py"
__version__	= "0.1"

## ToDo
#
# dashboard showing daily/monthly stats ?
# console mode
# add data from json (=> conversion to parquet)
# add data from parquet
# ordering by domaine ? 
# indicated first and times that email has been seen ?
#
## End of ToDo

## Done list
#
# search match count for email
# search matches from a file (one email per line)
#
## End of Done list

## Imports ##
from optparse import OptionParser
import sys
import curses
import httplib2
import urllib
import json
import operator

headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; rv:25.0) Gecko/20100101 Firefox/25.0'}
data_folder = '/tmp/'
options = None

## Params ##
def get_params():
	parser = OptionParser()
        parser.add_option('-e', '--email', dest='email', default='', help='Search an email')
        parser.add_option('-f', '--file', dest='file', default='', help='Search from a file (one email per line)')
        parser.add_option('', '--console', dest='console', default=False, action='store_true', help='Give me a console')
        parser.add_option('-v', '--verbose', dest='debug', default=False, action='store_true', help='Debug mode')
        parser.add_option('', '--host', dest='host', default='127.0.0.1:8047', help='Host address and port')
        parser.add_option('-o', '--output', dest='output', default='', help='file to store results')

	(options, args) = parser.parse_args(sys.argv)
	return options

def debug(message):
    if options.debug:
        print '[debug] %s' % message

def output(message):
    print message
    if options.output != '':
        options.output_handler.write(message)
        f.close()
        

def search_email(email):
    debug('Searching email : %s'%email)
    request = 'SELECT * FROM dfs.`%s/*.json` WHERE LOWER(email) LIKE LOWER(\'%%%s%%\')' % (data_folder, email)
    debug(request)
    resp = send_request(request)
    return resp
        
def send_request(request):
    http = httplib2.Http()
    headers['Content-Type'] = 'application/json; charset=UTF-8'

    request.replace('"','\\"')
    body = {'queryType':'SQL', 'query':request}
    resp, data = http.request('http://%s/query.json'%options.host, 'POST', headers=headers, body=json.dumps(body))

    return json.loads(data)


def console():
    print '## ToDo : console ##'


## Main ##
if __name__ == '__main__':
	options = get_params()

        if options.output != '':
            try:
                debug('enabling output to the file %s' % options.output)
                options.output_handler = open(options.output, 'w')
            except:
                print 'Error during opening the output file (%s)' % options.output
                sys.exit()

        if options.console:
            debug('enabling console')
            console()
            sys.exit()

        # global results_count variable for email and file options
        results_count = dict()

        if options.email != '':
            debug('processing "email" option')
            results = search_email(options.email)
            results = results['rows']
            if results[0] == {}:
                # no result
                results_count[options.email] = 0
            else:
                results_count[options.email] = len(results)


        if options.file != '':
            debug('processing "file" option')
            debug('opening file %s'%options.file)


            with open(options.file, 'r') as fp:
                for cnt, line in enumerate(fp):
                    line = line.rstrip()
                    results = search_email(line)
                    results = results['rows']
                    if results[0] == {}:
                        # no result
                        results_count[line] = 0
                    else:
                        results_count[line] = len(results)

        # print results
        results_count = sorted(results_count.items(), key=operator.itemgetter(1))
        results_count.reverse()
        print results_count
