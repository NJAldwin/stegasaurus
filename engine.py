#!/usr/bin/python

import wave, mimetypes, os, random, sys
from struct import unpack, pack
from numpy.fft import rfft, irfft
from numpy import int16
from bits import testbit, setbit

# Constants
SEED = "our cool awesome seed"  # random number generator seed
FRAMEDIST = 7
LOW_LOW_MASK = 0x000000FF   # used for masking off the upper and lower segments of bytes
HIGH_LOW_MASK = 0x00FF0000
LOW_HIGH_MASK = 0x0000FF00   # used for masking off the upper and lower segments of bytes
HIGH_HIGHT_MASK = 0xFF000000
UNIQUE_LEFT = -42       # used when checking for steganographic payload
UNIQUE_RIGHT = 42
CHUNK_SIZE = 64

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
        #frame = unpack("<hh", inaudio.readframes(1))
        chunk = unpack('<' + 'h'*2*CHUNK_SIZE, inaudio.readframes(CHUNK_SIZE))
        left = [ chunk[i] for i in range(0,len(chunk),2) ]
        right = [ chunk[i] for i in range(1,len(chunk),2) ]
        
        #freqs = fft(frame)
        left_freqs = rfft(left)
        right_freqs = rfft(right)

        bucket = len(left_freqs)/2 + 1
        left_freqs[bucket] = left_freqs[bucket-1] + (-1 if prbits[i] else 0)

        # write new frame for output audio
        new_left = irfft(left_freqs)
        new_right = irfft(right_freqs)
        outframe = []
        for i in range(len(new_left)):
            outframe += [ new_left[i] ]
            outframe += [ new_right[i] ]
        #print "%s:%s:%s" % (frame,prbits[i],newframes)
        outaudio.writeframes(pack('<' + 'h'*2*CHUNK_SIZE, *outframe))

    outaudio.close()
    inaudio.close()

def markunique(end):
    """ Adds unique marking and length """
    # Separate the end of the file into the upper and lower 16 bits.
    endlolo = end & LOW_LOW_MASK
    endlohi = (end & LOW_HIGH_MASK) >> 8
    endhilo = (end & HIGH_LOW_MASK) >> 16
    endhihi = (end & HIGH_HIGHT_MASK) >> 24

    # Put the metadata into the first two frames
    # The first frame's two channels sum to 0, indicating there is data stored in the file
    # The second frame's two channels contain the length of the steganographic payload
    # some pack() usage notes:
    # < : little-endian
    # h : short
    # H : unsigned short
    return pack("<hhhh", endlolo, endlohi, endhilo, endhihi)

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
    #checkunique(inaudio.readframes(1))

    frame = unpack("<hhhh", inaudio.readframes(2))
    totalframes = inaudio.getnframes()
    end = frame[0] | (frame[1] << 8) | (frame[2] << 16) | (frame[3] << 24)
    dist = (totalframes / end) - 2
    bits = []
    for i in range(end): # inaudio.tell() < totalframes and len(bits) < end:
        chunk = unpack('<' + 'h'*2*CHUNK_SIZE, inaudio.readframes(CHUNK_SIZE))
        left = [ chunk[i] for i in range(0,len(chunk),2) ]
        right = [ chunk[i] for i in range(1,len(chunk),2) ]
        
        #freqs = fft(frame)
        left_freqs = rfft(left)
        right_freqs = rfft(right)

        bucket = len(left_freqs)/2 + 1
        bit = 0 if left_freqs[bucket-1] - left_freqs[bucket] == 0 else 1
#print left_freqs[bucket-1], left_freqs[bucket]

        bits.append(bit)
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

