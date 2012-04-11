#!/usr/bin/python

import wave, mimetypes, os, random, sys
from struct import unpack, pack
from numpy.fft import fft, ifft
from numpy import int16
from bits import testbit, setbit

# Constants
SEED = "our cool awesome seed"  # random number generator seed
FRAMEDIST = 7
LOW_MASK = 0x0000FFFF   # used for masking off the upper and lower segments of bytes
HIGH_MASK = 0xFFFF0000
UNIQUE_LEFT = -42       # used when checking for steganographic payload
UNIQUE_RIGHT = 42

random.seed(SEED)       # seeds the random generator

def encode(opts):
    """ Encodes data into a file """
    print "Encoding..."
    file1, file2, file3 = opts  # pull the individual values out of the opts array

    # If the carrier doesn't exist, show the usage
    if not os.path.isfile(file2):
        print >>sys.stderr, 'ERROR: Payload file %s does not exist!' % file2
        exit()

    # opens up the payload file and generate random bits
    tohide = open(file2, 'rb').read()
    bytes = bytearray(tohide)
    bits = []
    for b in bytes:
        for i in range(8):
            bits.append(testbit(b,i))
    prbits = [b ^ random.getrandbits(1) for b in bits]

    # copying the input audio's properties over to the output
    inaudio = wave.open(file1, 'rb')
    outaudio = wave.open(file3, 'wb')
    outaudio.setparams(inaudio.getparams())

    # Find the total number of frames in the input file
    totalframes = inaudio.getnframes()

    # The end of the file occurs at the end of the prbits array if it is shorter than the
    # length of the original file. Otherwise, it is at the end of the original file.
    end = len(prbits) if len(prbits) * FRAMEDIST < totalframes else (totalframes/FRAMEDIST)

    # Calculate the distance to the end of the file
    dist = (totalframes / end) - 2

    # skip first 2 frames (contains metadata) for unique marking & length
    inaudio.readframes(2)
    outframe = markunique(end) 
    outaudio.writeframes(outframe)

    # TODO: Convert this process to spread-spectrum
    # For each frame to the end of the file
    for i in range(end):
        # grab current input audio frame
        frame = unpack("<hh", inaudio.readframes(1))
        freqs = fft(frame)
        side = (i % 2) == 0 # alternate channels
        freqs[0] = prbits[i] if side else freqs[0]
        freqs[1] = freqs[1] if side else prbits[i]

        # write new frame for output audio
        newframes = ifft(freqs)
        #print "%s:%s:%s" % (frame,prbits[i],newframes)
        outframe = pack("<hh", newframes[0], newframes[1])
        outaudio.writeframes(outframe)

        frames = bytearray(inaudio.readframes(dist))
        outaudio.writeframes(frames)

    frames = bytearray(inaudio.readframes(totalframes))
    outaudio.writeframes(frames)

    outaudio.close()
    inaudio.close()

def markunique(end):
    """ Adds unique marking and length """
    # Separate the end of the file into the upper and lower 16 bits.
    endlo = end & LOW_MASK
    endhi = (end & HIGH_MASK) >> 16

    # Put the metadata into the first two frames
    # The first frame's two channels sum to 0, indicating there is data stored in the file
    # The second frame's two channels contain the length of the steganographic payload
    # some pack() usage notes:
    # < : little-endian
    # h : short
    # H : unsigned short
    return pack("<hhHH", UNIQUE_LEFT, UNIQUE_RIGHT, endlo, endhi)

def checkunique(mark):
    check = unpack("<hh", mark)
    if not check[0]==UNIQUE_LEFT and not check[1]==UNIQUE_RIGHT and not check[0]+check[1]==0:
        print >>sys.stderr, "ERROR: No steganographic payload found."
        outmsg.close()
        exit()

def decode(opts):
    """ Decode data from a file """
    print "Decoding..."
    file4, file5 = opts

    inaudio = wave.open(file4, 'rb')
    outmsg = open(file5, 'wb')

    # check unique
    checkunique(inaudio.readframes(1))

    frame = unpack("<HH", inaudio.readframes(1))
    totalframes = inaudio.getnframes()
    end = frame[0] | (frame[1] << 16)
    dist = (totalframes / end) - 2
    bits = []
    i=0
    while inaudio.tell() < totalframes and len(bits) < end:
        frame = unpack("<hh", inaudio.readframes(1))
        side = (i % 2) == 0
        freqs = fft(frame)
        bits.append(freqs[0 if side else 1].astype(int16))
        inaudio.readframes(dist)        # skip frames
        i += 1
    inaudio.close()

    debits = [b ^ random.getrandbits(1) for b in bits]
    debytes = []
    for i in range(0,len(debits),8):
        byte = 0
        for j in range(8):
            if (debits[i+j] == 1):
                byte = setbit(byte, j)
        debytes.append(byte)

    outmsg.write(bytearray(debytes))
    outmsg.close()

