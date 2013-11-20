#!/usr/bin/env python
#coding=utf8
__author__	= "haxom"
__email__	= "haxom@haxom.net"
__file__	= "bruty.py"
__version__	= "0.1"

## Imports ##
from optparse import OptionParser
from os import path
import sys
import curses

## Params ##
def getParams():
	parser = OptionParser()
	parser.add_option('', '--files', dest='filenames', default='', help='PATH to filenames wordilist')
	parser.add_option('', '--directories', dest='directories', default='',  help='PATH to directories wordlist')
	parser.add_option('', '--patator', dest='patator', default='', help='PATH to patator.py script')
	parser.add_option('', '--url', dest='url', default='http://localhost', help='based URL (without FILEX text)')
	parser.add_option('', '--options', dest='options', help='options provided to patator.py')
	parser.add_option('', '--log', dest='log', default=False, action='store_true', help='enable log of patator (-l) with dynamic name destination')
	parser.add_option('', '--level', dest='level', default=-1, help='subdirectories max. level (<0 = infinite)')
	global options
	(options, args) = parser.parse_args(sys.argv)

def display(x, y, text):
	stdscr.addstr(x, y, text)
	stdscr.refresh()

## Main ##
if __name__ == '__main__':
	stdscr = curses.initscr()
	curses.noecho()

	display(0, 0, '__________                __          ')
	display(1, 0, '\______   \_______ __ ___/  |_ ___.__.')
	display(2, 0, ' |    |  _/\_  __ \  |  \   __<   |  |')
	display(3, 0, ' |    |   \ |  | \/  |  /|  |  \___  |')
	display(4, 0, ' |______  / |__|  |____/ |__|  / ____|')
	display(5, 0, '        \/                     \/     ')
	display(6, 0, '                                  v%s'%__version__)

	display(8, 0, '* Analysing parameters ...')
	getParams()
	options.level = int(options.level)
	if len(options.filenames) <= 0 or not path.exists(options.filenames):
		options.filenames = ''
	if len(options.directories) <= 0 or not path.exists(options.directories):
		options.directories = ''

	if options.directories == '' and options.filenames == '':
		display(9, 0, 'Both --files and --directories are empty or invalid !')
		sys.exit()
	if not path.exists(options.patator):
		display(9, 0, '--patator is empty or invalid !')
		sys.exit()

	display(8, 0, '| Target: %s' % options.url)
	display(9, 0, '| Filenames based on: %s' % options.filenames)
	display(10, 0, '| Directories based on: %s' % options.directories)
	display(11, 0, '| Level of subdirectories scanned: %d' % options.level)

	results = dict()
