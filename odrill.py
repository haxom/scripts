#!/usr/bin/env python
#coding=utf8
__author__	= "haxom"
__email__	= "haxom@haxom.net"
__file__	= "odrill.py"
__version__	= "0.3"

## ToDo
#
# console mode
# indicated first and times that email has been seen ?
# web interface
## add data from json
## add data from parquet
## dashboard / stats
#
## End of ToDo

## Done list
#
# search match count for email
# search matches from a file (one email per line)
# manage following information : date / RM / password
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
import SocketServer
import SimpleHTTPServer

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
        parser.add_option('-p', '--password', dest='password', default=False, action='store_true', help='Enable password processing')
        parser.add_option('-w', '--web', dest='web', default=False, action='store_true', help='Launch web service')

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
    request = 'SELECT * FROM dfs.`%s/*.parquet` WHERE LOWER(Mail) LIKE LOWER(\'%%%s%%\') ORDER BY `RM` ASC' % (data_folder, email)
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

def webserver():
    handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    httpd = SocketServer.TCPServer(('127.0.0.1', 8888), handler)
    print 'Web server launched. Listenning on 127.0.0.1:8888'
    httpd.serve_forever()


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

        if options.web:
            debug('launching web server...')
            webserver()
            sys.exit()

        if options.console:
            debug('enabling console')
            console()
            sys.exit()

        # results_output will store all results
        results_output = dict()

        if options.email != '':
            debug('processing "email" option')
            results = search_email(options.email)
            results = results['rows']
            if results[0] == {}:
                # no result
                results_output[options.email] = {'count':0, 0:{'rm':'', 'date':'', 'pass':'', 'entite':''}}
            else:
                results_output[options.email] = {'count':len(results)}
                for i in range(len(results)):
                    results_output[options.email][i] = {'rm':results[i]['RM'], 'date':results[i]['Date'], 'entite':results[i]['Entite'], 'pass':results[i]['Password']}

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
                        results_output[line] = {'count':0, 0:{'rm':'', 'date':'', 'pass':''}}
                    else:
                        results_output[line] = {'count':len(results)}
                        for i in range(len(results)):
                            results_output[line][i] = {'rm':results[i]['RM'], 'date':results[i]['Date'], 'entite':results[i]['Entite'], 'pass':results[i]['Password']}

        # print results
        results_output = sorted(results_output.items(), key=operator.itemgetter(1))
        results_output.reverse()
        for r in results_output:
            print '* %s' % r[0]
            for i in range(r[1]['count']):
                if options.password:
                    print '  - RM%s (%s / %s) : %s'%(r[1][i]['rm'], r[1][i]['date'], r[1][i]['entite'], r[1][i]['pass'])
                else:
                    print '  - RM%s (%s / %s)'%(r[1][i]['rm'], r[1][i]['entite'], r[1][i]['date'])

