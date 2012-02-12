import sndhdr
import wave
import mimetypes
import getopt
import sys
import os
import numpy
from numpy.fft import fft, ifft
from numpy import array
import random

DECODE = "decode"
ENCODE = "encode"
WAV = "wav"
RATE = 44100
SEED = "our cool awesome seed"
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

    while inaudio.tell()<totalframes:
        print "%s / %s" % (inaudio.tell(), totalframes)
        frames = bytearray(inaudio.readframes(NFRAMES))
        if byteloc < len(prbytes):
            freqs = fft(frames)
            writebytes = prbytes[byteloc:byteloc+32]
            byteloc += 32
            freqs = modulate(freqs, writebytes, 64, len(prbytes))
            l = ifft(freqs).round().clip(0,255).astype(int).tolist()
            frames = bytearray(l)
        outaudio.writeframes(frames)

    outaudio.close()
    inaudio.close()

def modulate(freqs, new, start, end):
    j = 0
    for i in range(start, 1 + (end if end < len(new) else len(new)), 2):
        j = (j + 1) % len(new)
        freqs[i] = freqs[i] + new[j]
    return freqs.clip(-32767, 32767)

def decode(opts):
    print "decoding, woo"
    file4 = opts[0]
    file5 = opts[1]
    #debytes = [b ^ random.getrandbits(8) for b in prbytes]
    #print "debytes"
    #print debytes

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
