#!/usr/bin/python3
import urllib.request
import json
import struct
import binascii
import hashlib
import sys
import re
import time

import sha256

ux = binascii.unhexlify
hx = binascii.hexlify
def _sha256(x):
    #return hashlib.sha256(x).digest()
    return sha256.sha256(x).digest()

def _sha256d(x, record_schedule=False):
    if record_schedule:
        sha256.record_schedule()
        return _sha256(_sha256(x)), sha256.get_record()
    else:
        return _sha256(_sha256(x))

# Fetch last successful block from blockchain.info
def fetch(url):
    return urllib.request.urlopen(url).read().decode('utf-8')

#Use the example from bitcoin wiki
#latestblock_hash = '00000000000000001e8d6829a8a21adc5d38d0a473b144b6765798e61f98bd1d'
latestblock_hash = json.loads(fetch("https://blockchain.info/latestblock"))['hash']
print("using " + latestblock_hash)
latestblock = json.loads(fetch("https://blockchain.info/rawblock/" + latestblock_hash))
#print(latestblock)

def reconstruct_block(latestblock, nonce_override = None):
    # Grab values from block, convert to binary
    # Various endianness crap must be done

    version = latestblock['ver']
    version = struct.pack('<I', version)
    prevblock = latestblock['prev_block']
    prevblock = ux(prevblock)[::-1]
    merkle = latestblock['mrkl_root']
    merkle = ux(merkle)[::-1]
    time = latestblock['time']
    time = struct.pack('<I', time)
    bits = latestblock['bits']
    bits = struct.pack('<I', bits)
    nonce = latestblock['nonce'] if nonce_override is None else nonce_override
    nonce = struct.pack('<I', nonce)

    reconstructed_block = version + prevblock + merkle + time + bits + nonce
    return reconstructed_block
reconstructed_block = reconstruct_block(latestblock)
print("Block header (before mangling):", \
    hx(reconstructed_block).decode('ascii'))
computed_hash = hx(_sha256d(reconstructed_block)[::-1]).decode('ascii')
print("Hash of header: " + computed_hash)
#nonce = latestblock['nonce']
#print("Winning nonce: " + str(nonce))
_, schedules = _sha256d(reconstructed_block, True)
# The first message schedule is irrelevant because of midstate
# The second message expansion is the part we're trying to optimize

def format_expansion(schedules):
    exp = schedules[1]
    exp = b''.join(map(lambda x: struct.pack("!I", x), exp))
    exp = hx(exp).decode('ascii')
    exp = re.sub("(.{64})", "\\1\n", exp, 0, re.DOTALL)
    return exp
expansion = format_expansion(schedules)
print("Winning expansion of 2nd chunk\n" + expansion)
print("Trying all expansions...")

# Try all nonces, one at a time.
nonce = 0
while True:
    block_header = reconstruct_block(latestblock, nonce)
    _, schedules = _sha256d(block_header, True)
    expansion = format_expansion(schedules)
    chars = len(expansion)
    print(nonce)
    print(expansion)
    time.sleep(0.1)
    sys.stdout.write('\n' * 30)
    nonce += 1

