#!/usr/bin/env python
#coding=utf8
__author__	= "haxom"
__email__	= "haxom@haxom.net"
__file__	= "odrill.py"
__version__	= "0.4"

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
import httplib2
import urllib
import json
import operator

# web interface
import BaseHTTPServer
import SocketServer
import urlparse
import urllib

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

## {{ Printers methods
def debug(message):
    if options.debug:
        print '[debug] %s' % message

def output(message):
    print message
    if options.output != '':
        options.output_handler.write(message)
        f.close()
## }}
        
## {{ Int. methods
def search_one(email):
    results_output = dict()
    results = search_email(email)
    results = results['rows']
    if results[0] == {}:
        # no result
        results_output[email] = {'count':0, 0:{'rm':'', 'date':'', 'pass':'', 'entite':''} }
    else:
        results_output[email] = {'count':len(results) }
        for i in range(len(results)):
            results_output[email][i] = {'rm':results[i]['RM'], 'date':results[i]['Date'], 'entite':results[i]['Entite'], 'pass':results[i]['Password']}
    return results_output

def search_file(f):
    results_output = dict()
    with open(f, 'r') as fp:
        for cnt, line in enumerate(fp):
            line = line.rstrip()
            results = search_email(line)
            results = results['rows']
            if results[0] == {}:
                # no result
                results_output[line] = {'count':0, 0:{'rm':'', 'date':'', 'pass':''} }
            else:
                results_output[line] = {'count':len(results)}
                for i in range(len(results)):
                    results_output[line][i] = {'rm':results[i]['RM'], 'date':results[i]['Date'], 'entite':results[i]['Entite'], 'pass':results[i]['Password']}
    return results_output

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

## }}

## {{ Console

def console():
    print '## ToDo : console ##'

## }}

## {{ Web Server
class WebServer(BaseHTTPServer.BaseHTTPRequestHandler):
    is_post = False

    def set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()


    def html_headers(self):
        self.wfile.write('<html>\n<head>\n')
        css_html = """
<style>
body {margin: 10; font-family: "Merriweather", sans-serif; font-size: 1rem; font-weight: 400; line-height: 1.9; color: #999; text-align: left; background-color: #fff;}
hr {box-sizing:  content-box; height: 0; overflow: visible;}
h1, h2, h3, h4, h5, h6 {margin-top: 0; margin-bottom: 1rem; color: #333}
p {margin-top: 0; margin-bottom: 1rem;}
hr {box-sizing: content-box; height: 0; overflow: visible;}
img {vertical-align: middle; border-style: none;}
table {border-collapse: collapse;}
label {display: inline-block; margin-bottom: .5rem;}
button {border-radius: 0;}
button:focus {outline: 1px dotted; outline: 5px auto -webkit-focus-ring-color;}
input, button, select, optgroup, textarea {margin: 0; font-family: inherit; font-size: inherit; line-height: inherit;}
button, input {overflow: visible;}
textarea {overflow: auto; resize: vertical;}
code {padding: 0.2rem 0.4rem; font-size: 90%; color: #bd4147; background-color: #f8f9fa; border-radius: 0px;}
.navbar-text {display: inline-block; padding-top: 0.5rem; padding-bottom: 0.5rem;}
.navbar-collapse {flex-basis: 100%; flex-grow: 1; align-items: center;}
.navbar-light, .navbar-nav, .navbar-link, .dropdown-item {color: #fff; background-color: #acacac; font-weight: bold;  padding: 1rem 2rem !important; font-size: 0.9rem;}
.btn {display: inline-block; font-weight: 400; text-align: center; white-space: nowrap; vertical-align: middle; user-select: none; border: 1px solid transparent; padding: 0.375rem 0.75rem; font-size: 1rem; line-height: 1.9; border-radius: 0px; transition: background-color 0.15s ease-in-out, border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out; }
.btn-primary {color: #fff; background-color: #333; border-color: #333;}
.btn-primary:hover {color: #fff; background-color: #202020; border-color: #1a1a1a;}
.btn-primary:focus {box-shadow: 0 0 0 0.2rem rgba(51, 51, 51, 0.5);}
.btn-primary:disabled {background-color: #333; border-color: #333;}
.btn-primary:not {color: #fff; background-color: #1a1a1a; border-color: #131313; box-shadow: 0 0 0 0.2rem rgba(51, 51, 51, 0.5);}
.footer-lists {background-color: #ebebeb; padding: 2rem; margin-bottom: 1rem; border-top: 1px solid #d2d2d2; font-size: 0.8rem}
.footer-lists h4 {color #999999}
hr {box-sizing: content-box; height: 0; overflow: visible;}
</style>
        """
        self.wfile.write(css_html)
        self.wfile.write('</head>\n<body>\n')


    def html_footers(self):
        self.wfile.write('</body>\n</html>\n')

    def do_GET(self):
        parsed_path = urlparse.urlparse(self.path)
        params_tmp = parsed_path.query.split(';')
        params = list()
        for p in params_tmp:
            params.append(p.split('='))

        self.set_headers()
        self.html_headers()
        self.wfile.write('\n')

        # title
        self.wfile.write('<center><h1>ODRILL v%s</h1></center>\n'%__version__)

        # top bar
        topbar_html = """
<div class="collapse navbar-collapse"><ul class="navbar-nav mr-auto">
<center>
<form method="get" action="odrill.py" style="display: inline;">
<input size="25" placeholder="bla@bla.com" type="text" name="search_term"> 
<button class="btn btn-primary" type="submit">recherche</button></form> | 
<form enctype="multipart/form-data" method="post" action="odrill.py" style="display: inline;">
<input size="5" type="file" name="search_term_file">
<button class="btn btn-primary" type="submit">envoi et recherche</button></form>
</center></ul></div>
        """
        self.wfile.write(topbar_html)

        # results
        self.wfile.write('<div class="footer-lists">\n')
        self.wfile.write('<center><h4>Résultats</h4></center>\n')
        self.wfile.write('<hr>')
        
        # only one term
        for p in params:
            if 'search_term' in p:
                search_term = urllib.unquote(p[1])
                self.wfile.write('Terme recherché : %s\n' % search_term)
                self.wfile.write('<hr>\n')
                results = search_one(search_term)
                results = sorted(results.items(), key=operator.itemgetter(1))
                results.reverse()
                for r in results:
                    self.wfile.write('[%s]<br />\n' % r[0])
                    if r[1]['count'] == 0:
                        self.wfile.write('<b><i>Aucun résultat</i></b><br />\n')
                    for i in range(r[1]['count']):
                        if options.password:
                            self.wfile.write('RM%s (%s / %s) : %s<br />\n'%(r[1][i]['rm'], r[1][i]['date'], r[1][i]['entite'], r[1][i]['pass']))
                        else:
                            self.wfile.write('RM%s (%s / %s)<br />\n'%(r[1][i]['rm'], r[1][i]['entite'], r[1][i]['date']))

        # file-terms
        if self.is_post:
            data_len = int(self.headers['Content-Length'])
            read_len = 0
            data_bound = self.rfile.readline() + self.rfile.readline() + self.rfile.readline() + self.rfile.readline()
            read_len += len(data_bound)
            data_bound_s = data_bound.split('\n')[0][:-1]
            filename = data_bound[data_bound.find('filename')+8+2:data_bound.find('"', data_bound.find('filename')+8+2+1)]

            f = open('%s/odrill_upload.txt'%data_folder, 'w')
            count = 0
            before = self.rfile.readline()
            data = self.rfile.readline()
            read_len += len(before) + len(data)
            while read_len < data_len:
                count += 1
                f.write(before)
                before = data
                data = self.rfile.readline()
                read_len += len(data)
            f.close()
            self.wfile.write('Fichier : %s (%d entrées) <br />\n' % (filename, count))

            results = search_file('%s/odrill_upload.txt'%data_folder)
            results = sorted(results.items(), key=operator.itemgetter(1))
            results.reverse()
            for r in results:
                self.wfile.write('[%s]<br />\n' % r[0])
                if r[1]['count'] == 0:
                    self.wfile.write('<b><i>Aucun résultat</i></b><br />\n')
                for i in range(r[1]['count']):
                    if options.password:
                        self.wfile.write('RM%s (%s / %s) : %s<br />\n'%(r[1][i]['rm'], r[1][i]['date'], r[1][i]['entite'], r[1][i]['pass']))
                    else:
                        self.wfile.write('RM%s (%s / %s)<br />\n'%(r[1][i]['rm'], r[1][i]['entite'], r[1][i]['date']))

        self.wfile.write('<hr>')
        self.wfile.write('</div>')


        self.wfile.write('\n')
        self.html_footers()
        self.is_post = False

    def do_POST(self):
        self.is_post = True
        self.do_GET()

def run_webserver():
    server = BaseHTTPServer.HTTPServer
    handler = WebServer
    print 'Web server launched. Listenning on 127.0.0.1:8888'
    httpd = server(('127.0.0.1', 8888), handler)
    httpd.serve_forever()
## }}

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
            run_webserver()
            sys.exit()

        if options.console:
            debug('enabling console')
            console()
            sys.exit()

        # results_output will store all results
        results_output_one = dict()
        results_output = dict()
        
        if options.email != '':
            debug('processing "email" option')
            results_output_one = search_one(options.email)

        if options.file != '':
            debug('processing "file" option')
            debug('opening file %s'%options.file)
            results_output = search_file(options.file)

        results = results_output_one
        results.update(results_output)

        # print results
        results = sorted(results.items(), key=operator.itemgetter(1))
        results.reverse()
        for r in results:
            print '* %s' % r[0]
            for i in range(r[1]['count']):
                if options.password:
                    print '  - RM%s (%s / %s) : %s'%(r[1][i]['rm'], r[1][i]['date'], r[1][i]['entite'], r[1][i]['pass'])
                else:
                    print '  - RM%s (%s / %s)'%(r[1][i]['rm'], r[1][i]['entite'], r[1][i]['date'])
