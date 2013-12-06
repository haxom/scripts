#!/usr/bin/env python
#coding=utf8
__author__	= "haxom"
__email__	= "haxom@haxom.net"
__file__	= "bruty.py"
__version__	= "0.4"

## Imports ##
from optparse import OptionParser
from os import path
import sys
import curses
from time import sleep
from threading import Thread, active_count
import Queue
import httplib2
from math import ceil

headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; rv:25.0) Gecko/20100101 Firefox/25.0'}

## Params ##
def getParams():
	parser = OptionParser()
	parser.add_option('-f', '--files', dest='filenames', default='', help='PATH to filenames wordilist')
	parser.add_option('-d', '--directories', dest='directories', default='',  help='PATH to directories wordlist')
	parser.add_option('-u', '--url', dest='url', default='http://localhost', help='based URL (without FILEX text)')
	parser.add_option('-H', '--headers', dest='headers', default='', help='custom the headers (name:value;name:value...)')
	parser.add_option('-l', '--log', dest='log', default=False, action='store_true', help='log the requests/responses')
	parser.add_option('-x', '--exclude', dest='exclude', default='404', help='exclude return code, separated by a coma')
	parser.add_option('', '--level', dest='level', default=-1, help='subdirectories max. level (< 0 = infinite)')
	parser.add_option('-m', '--method', dest='method', default='GET', help='HTTP method (default: GET)')
	parser.add_option('-n', '--thread', dest='threads', default=1, help='Nbre of threads')
	(options, args) = parser.parse_args(sys.argv)
	return options

def display(x, y, text):
	stdscr.addstr(x, y, text)
	stdscr.refresh()

def displayTree(tree, x):
	display(x, 0, 'ToDo')

def search(options, candidates, queue, root):
	http =  httplib2.Http()
	for current in candidates:
		current = current.rstrip()
		response, content = http.request('%s/%s/%s' % (options.url, root, current), options.method, headers=headers)
		if str(response.status) not in options.exclude:
			queue.put((response.status, current))

def getElements(options, dico, root, queue):
	num_lines = sum(1 for line in open(dico))
	f = open(dico)
	pas = int(ceil(num_lines*1./options.threads))
	for i in range(0, options.threads):
		current_list = list()
		beg = i*pas
		end = (i+1)*pas
		if i == options.threads -1:
			end = num_lines
		for i in range(beg, end):
				current_list.append(f.readline())
		t = Thread(target=search, args=(options, current_list, queue, root), kwargs=None)
		t.setDaemon(True)
		t.start()
	f.close()
	while active_count() > 2:
		sleep(0.5)

## Main ##
if __name__ == '__main__':
	options = getParams()
	options.level = int(options.level)
	options.threads = int(options.threads)
	if options.threads < 1:
		options.threads = 1
	if len(options.filenames) <= 0 or not path.exists(options.filenames):
		options.filenames = ''
	if len(options.directories) <= 0 or not path.exists(options.directories):
		options.directories = ''
	options.exclude = options.exclude.split(',')
	if len(options.headers) != 0:
		headers = dict()
		for entry in options.headers.split(';'):
			nv = entry.split(':')
			if nv[0].lower() in 'User-Agent':
				headers.update({'User-Agent':nv[1]})
			else:
				headers.update({nv[0]:nv[1]})

	if options.directories == '' and options.filenames == '':
		print 'Both --files and --directories are empty or invalid !'
		sys.exit()

	stdscr = curses.initscr()
	curses.noecho()

	display(0, 0, '__________                __          ')
	display(1, 0, '\______   \_______ __ ___/  |_ ___.__.')
	display(2, 0, ' |    |  _/\_  __ \  |  \   __<   |  |')
	display(3, 0, ' |    |   \ |  | \/  |  /|  |  \___  |')
	display(4, 0, ' |______  / |__|  |____/ |__|  / ____|')
	display(5, 0, '        \/                     \/     ')
	display(6, 0, '                                  v%s'%__version__)

	display(8, 0, '| Target: %s' % options.url)
	display(9, 0, '| Filenames based on: %s' % options.filenames)
	display(10, 0, '| Directories based on: %s' % options.directories)
	display(11, 0, '| Level of subdirectories scanned: %d' % options.level)

	display(13, 0, '| Dictionnary attack ...')

	try:

		cur_lvl = 0
		tree = list()

		while cur_lvl <= options.level or options.level < 0:
			
			# files
			queue = Queue.Queue()
			getElements(options, options.filenames, '/', queue)
			while queue.qsize() > 0:
				cur = queue.get()
				tree.append(('f%d'%cur[0], cur[1]))

			# directories
			getElements(options, options.directories, '/', queue)
			while queue.qsize() > 0:
				cur = queue.get()
				tree.append(('d%d%s'%(cur[0],cur[1]), list()))


			cur_lvl+=1
		display(13, 0, '                        ')
		displayTree(tree, 14)
		print tree

	except Exception as e:
		print 'Error: %s' % e
