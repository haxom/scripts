#!/bin/env python
#coding=utf8
__author__      = "haxom"
__email__       = "haxom@haxom.net"
__file__        = "hash_search.py"
__version__     = "1"


import hashlib

form = 'sha1'
dico = 'rockyou.txt'
patterns = ['272d2d20', '272320', '272f2a20', '27613d']

f = open(dico, 'r')

for w in f:
    w = w[:-1]
    m = hashlib.new(form)
    m.update(w)
    hx = m.hexdigest()
    for p in patterns:
        if hx[:len(p)] == p:
            print '%s found with word %s' % (p, w)

f.close()
