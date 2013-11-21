#!/usr/bin/env python
#coding=utf8
__author__	= "haxom"
__email__	= "haxom@haxom.net"
__file__	= "bruty.py"
__version__	= "0.2"

## Imports ##
from optparse import OptionParser
from os import path
import sys
import curses
#from subprocess import check_output as call
from subprocess import Popen as call
from subprocess import STDOUT
from subprocess import PIPE
from threading import Thread, active_count
import Queue

## Globals ##
waitingString = ('-', '\\', '|', '/')

## Params ##
def getParams():
	parser = OptionParser()
	parser.add_option('', '--files', dest='filenames', default='', help='PATH to filenames wordilist')
	parser.add_option('', '--directories', dest='directories', default='',  help='PATH to directories wordlist')
	parser.add_option('', '--patator', dest='patator', default='', help='PATH to patator.py script')
	parser.add_option('', '--url', dest='url', default='http://localhost', help='based URL (without FILEX text)')
	parser.add_option('', '--options', dest='options', default='', help='options provided to patator.py')
	parser.add_option('', '--log', dest='log', default=False, action='store_true', help='enable log of patator (-l) with dynamic name destination')
	parser.add_option('', '--level', dest='level', default=-1, help='subdirectories max. level (< 0 = infinite)')
	global options
	(options, args) = parser.parse_args(sys.argv)

def display(x, y, text):
	stdscr.addstr(x, y, text)
	stdscr.refresh()

def drawTree(tree):
	display(13, 0, tree)

def execCall(options, rest, queue):
	cmd = 'python %s http_fuzz %s url=%s/FILE0 0=%s' % (options.patator, options.options, options.url, rest)
	a = call([cmd], shell=True, stdout=PIPE, stderr=STDOUT)
	stdout, stderr = a.communicate()
	queue.put(stdout)

## Main ##
if __name__ == '__main__':
	getParams()
	options.level = int(options.level)
	if len(options.filenames) <= 0 or not path.exists(options.filenames):
		options.filenames = ''
	if len(options.directories) <= 0 or not path.exists(options.directories):
		options.directories = ''

	if options.directories == '' and options.filenames == '':
		print 'Both --files and --directories are empty or invalid !'
		sys.exit()
	if not path.exists(options.patator):
		print '--patator is empty or invalid !'
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

	results = dict()

	try:

		cur_lvl = 0
		while cur_lvl <= options.level or options.level < 0:
			# files
			queue = Queue.Queue()
			t1 = Thread(target=execCall, args=(options, options.filenames, queue), kwargs=None)
			t1.setDaemon(True)
			t1.start()

			c = 0
			display(13, 0, waitingString[c%4])
			while active_count() > 2:
				c+=1
				t2 = Thread(target=display, args=(13, 0, waitingString[c%4]), kwargs=None)
				t2.setDaemon(True)
				t2.start()
				t2.join()
				sleep(0.5)

			drawTree(queue.get())

			# directories
			#cmd = 'python %s http_fuzz %s url=%s/FILE0 0=%s' % (options.patator, options.options, options.url, options.directories)	

			cur_lvl+=1

	except Exception as e:
		print 'Error: %s' % e
