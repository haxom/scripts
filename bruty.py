#!/usr/bin/env python
#coding=utf8
__author__	= "haxom"
__email__	= "haxom@haxom.net"
__file__	= "bruty.py"
__version__	= "1.0b"

## ToDo
#
# + Recursion of the recursion (no limitation to 4 level (0 to 3))
# + More filters
# + Better display
# + Dynamic output export
#
## End of ToDo

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
from urllib import quote_plus

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
	parser.add_option('', '--level', dest='level', default=-1, help='subdirectories max. level (0 to 3)')
	parser.add_option('-m', '--method', dest='method', default='GET', help='HTTP method (default: GET)')
	parser.add_option('-n', '--thread', dest='threads', default=1, help='Nbre of threads')
	(options, args) = parser.parse_args(sys.argv)
	return options

def display(x, y, text):
	# clear lien before
	stdscr.addstr(x, 0, '                                                      ')
	stdscr.addstr(x, y, text)
	stdscr.refresh()

def displayTree(tree, x, decal=0):
	# print tree
	# return the next line number
	for i in tree:
		elem = i[0]
		if(elem[0] == 'f'):
			code = elem[1:4]
			name = i[1]
			display(x, decal, '| %s | %s'%(code, name))
		elif elem[0] =='d':
			code = elem[1:4]
			name = elem[4:]
			display(x, decal, '| %s | %s'%(code, name))
			subtree = i[1]
			if len(subtree) > 0:
				x += 1
				x = displayTree(subtree, x, 10+decal)
				x -= 1
		x += 1
	return x

def removeDouble(tree):
	new_tree = list()
	for i in tree:
		if new_tree.count(i) == 0:
			new_tree.append(i)
	return new_tree

def search(options, candidates, queue, root):
	http =  httplib2.Http()
	for current in candidates:
		current = current.rstrip()
		if len(current) == 0:
			continue
		response, content = http.request('%s%s%s' % (options.url, root, quote_plus(current)), options.method, headers=headers)
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

def recursion(options, tree, root, cur_lvl=0):
	list_tmp = list()
	for i in tree:
		if i[0][0] == 'd':
			list_tmp.append(i)
	for i in list_tmp:
		try:
			display(2, 0, '| Level : %d/%d |  Current folder : %s/%s/ (%d/%d)' % (cur_lvl, options.level, root, i[0][4:], list_tmp.index(i)+1, len(list_tmp)))
			n_tree = list()
			# files
			getElements(options, options.filenames, '%s/%s/'%(root, i[0][4:]), queue)
			while queue.qsize() > 0:
				cur = queue.get()
				n_tree.append(('f%d'%cur[0], cur[1]))
			# directories
			getElements(options, options.directories, '%s/%s/'%(root, i[0][4:]), queue)
			while queue.qsize() > 0:
				cur = queue.get()
				n_tree.append(('d%d%s'%(cur[0],cur[1]), list()))
			display(2, 0, '                                                                          ')
			n_tree = removeDouble(n_tree)
			tree[tree.index(i)] = (i[0], n_tree)
			displayTree(tree, 4)
		except curses.error:
			# sometimes... but anyway (maybe when trying to print out of screen)
			continue
	return tree

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

	display(0, 0, '[[ Bruty.py v%s ]]'%__version__)
	display(1, 0, '| Target: %s' % options.url)

	display(2, 0, '| Level : %d/%d | Current folder : / '%(0, options.level))

	try:
		tree = list()
		queue = Queue.Queue()

		## root research
		# files
		getElements(options, options.filenames, '/', queue)
		while queue.qsize() > 0:
			cur = queue.get()
			tree.append(('f%d'%cur[0], cur[1]))
		# directories
		getElements(options, options.directories, '/', queue)
		while queue.qsize() > 0:
			cur = queue.get()
			tree.append(('d%d%s'%(cur[0],cur[1]), list()))

		display(2, 0, '                                                                          ')
		tree = removeDouble(tree)
		displayTree(tree, 4)

		## recursive research
		cur_lvl = 1
		while cur_lvl <= options.level or options.level < 0:
				if cur_lvl == 1:
					tree = recursion(options, tree, '', 1) 
					displayTree(tree, 4)

				if cur_lvl == 2:
					for i in tree:
						if i[0][0] == 'd':
							index = tree.index(i)
							root = '/%s'%i[0][4:]
							new_list = recursion(options, i[1], root, 2)
							tree[index] = (i[0], new_list)
							displayTree(tree, 4)

				if cur_lvl == 3:
					for i in tree:
						if i[0][0] == 'd':
							index = tree.index(i)
							root = '/%s'%i[0][4:]
							for v in i[1]:
								if v[0][0] == 'd':
									index2 = i[1].index(v)
									root  = '%s/%s' % (root, v[0][4:])
									new_list = recursion(options, v[1], root, 3)
									i[1][index2] = (v[0], new_list)
							tree[index] = (i[0], i[1])
							displayTree(tree, 4)
				cur_lvl+=1
	except Exception as e:
		print 'Error: %s' % e
