import sndhdr
import wave
import mimetypes
import getopt
import sys
import os
import numpy
from numpy.fft import fft, ifft
from numpy import array
from struct import unpack, pack
import random

DECODE = "decode"
ENCODE = "encode"
WAV = "wav"
RATE = 44100
SEED = "our cool awesome seed"
FRAMEDIST = 7
NFRAMES = 32

def usage():
    print "usage"

def main():
    try:
        mode, opts = getopt.getopt(sys.argv[1:],"",[DECODE,ENCODE])
    except:
        usage()
        exit()
    if len(mode)<1:
        usage()
        exit()
    mode = mode[0][0].strip('-')
    print mode
    nargs = 3 if mode == ENCODE else 2
    if len(opts)<nargs:
        usage()
        exit()
    print opts
    if not checkformat(opts[0], WAV, RATE):
        usage()
        exit()
    random.seed(SEED)
    if mode == ENCODE:
        encode(opts)
    else:
        decode(opts)

def encode(opts):
    print "encoding, woo"
    file1 = opts[0]
    file2 = opts[1]
    file3 = opts[2]
    if not os.path.isfile(file2):
        usage()
        exit()
    # todo: RIFX STUFF
    tohide = open(file2, 'rb').read()
    inaudio = wave.open(file1, 'rb')
    bytes = bytearray(tohide)
    prbytes = [b ^ random.getrandbits(8) for b in bytes]
    outaudio = wave.open(file3, 'wb')
    outaudio.setparams(inaudio.getparams())
    totalframes = inaudio.getnframes()

    byteloc = 0

    end = len(prbytes) if len(prbytes) * FRAMEDIST < totalframes else (totalframes/7) 
    for i in range(end):
        frame = unpack("<hh", inaudio.readframes(1))
        freqs = fft(frame)
        freqs[0] = prbytes[i]
        l = ifft(freqs)
        outframe = pack("<hh", l[0], l[1])
        outaudio.writeframes(outframe)
        frames = bytearray(inaudio.readframes(128))
        outaudio.writeframes(frames)

    while inaudio.tell()<totalframes:
        frames = bytearray(inaudio.readframes(NFRAMES))
        outaudio.writeframes(frames)

    outaudio.close()
    inaudio.close()

def decode(opts):
    print "decoding, woo"
    file4 = opts[0]
    file5 = opts[1]
    inaudio = wave.open(file4, 'rb')
    outmsg = open(file5, 'wb')
    bytes = []
    totalframes = inaudio.getnframes()

    byteloc = 0

    
    while inaudio.tell()<totalframes:
        frame = unpack("<hh",inaudio.readframes(1))
        freqs = fft(frame)
        bytes.append(freqs[0].clip(0,255).astype(int))
        frames = bytearray(inaudio.readframes(128))

    inaudio.close()
    debytes = [b ^ random.getrandbits(8) for b in bytes]
    outmsg.write(bytearray(debytes))
    outmsg.close()

def checkformat(filename, expectedtype, expectedrate):
    if not os.path.isfile(filename):
        return False
    what = sndhdr.what(filename)
    # later: mp3 checking
    if what == None:
        return False
    ftype, rate, channels, frames, bps = what
    return ftype==expectedtype and rate==expectedrate

if __name__ == '__main__':
    main()
