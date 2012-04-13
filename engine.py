#!/usr/bin/python

import wave, mimetypes, os, random, sys
from audioformat import convertformat
from struct import unpack, pack, calcsize
from numpy.fft import rfft, irfft
from numpy import int16
from bits import testbit, setbit
from math import floor

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
BUCKETS_TO_USE = 6
BUCKET_OFFSET = 3

def reseed():
    """ Resets the random generator """
    random.seed(SEED)       # seeds the random generator

def encode(opts):
    """ Encodes data into a file """
    print "Encoding..."
    file1, file2, file3 = opts  # pull the individual values out of the opts array
    temp_outfile = file3[:-3]+'wav'

    # If the carrier doesn't exist, show the usage
    if not os.path.isfile(file2):
        print >>sys.stderr, 'ERROR: Payload file %s does not exist!' % file2
        exit()

    # opens up the payload file and generate random bits
    reseed()
    tohide = open(file2, 'rb').read()
    bytes = bytearray(tohide)
    bits = []
    for b in bytes:
        for i in range(8):
            bits.append(testbit(b,i))
    prbits = [b ^ random.getrandbits(1) for b in bits]

    # copying the input audio's properties over to the output
    inaudio = wave.open(file1, 'rb')
    outaudio = wave.open(temp_outfile, 'wb')
    outaudio.setparams(inaudio.getparams())

    # Find the total number of frames in the input file
    totalframes = inaudio.getnframes()

    lenprbits = len(prbits)
    # The end of the file occurs at the end of the prbits array if it is shorter than the
    # length of the original file. Otherwise, it is at the end of the original file.
    end = lenprbits if lenprbits * FRAMEDIST < totalframes else (totalframes/FRAMEDIST)

    # skip first 2 frames (contains metadata) for unique marking & length
    inaudio.readframes(2)
    outframe = pack_payload_length(end) 
    outaudio.writeframes(outframe)

    reseed()
    # For each 6 bits to encode
    for i in range(0, end, BUCKETS_TO_USE):
        # grab current input audio frame
        frames = inaudio.readframes(CHUNK_SIZE)
        structsize = CHUNK_SIZE*2
        chunk = unpack('<' + 'h'*structsize, frames)
        left = [ chunk[j] for j in range(0,len(chunk),2) ]
        right = [ chunk[j] for j in range(1,len(chunk),2) ]
        
        left_freqs = rfft(left)
        right_freqs = rfft(right)

        fbucket = len(left_freqs)/2 + 1
        for j in range(BUCKETS_TO_USE):
            bucket = fbucket + j*BUCKET_OFFSET
            if i+j < lenprbits:
                if prbits[i+j]:
                    left_freqs[bucket] = left_freqs[bucket-1] - 30
                else:
                    left_freqs[bucket] = left_freqs[bucket-1]

        # write new frame for output audio
        new_left = irfft(left_freqs)
        new_right = irfft(right_freqs)
        outframe = []
        for j in range(len(new_left)):
            outframe.append(new_left[j])
            outframe.append(new_right[j])
        outaudio.writeframes(pack('<' + 'h'*structsize, *outframe))

    frames = bytearray(inaudio.readframes(totalframes))
    outaudio.writeframes(frames)

    outaudio.close()
    inaudio.close()

    if file3[-3:] == 'mp3':
        convertformat(temp_outfile,'mp3')

def pack_payload_length(end):
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

def decode(opts):
    """ Decode data from a file """
    print "Decoding..."
    file4, file5 = opts

    inaudio = wave.open(file4, 'rb')
    outmsg = open(file5, 'wb')

    totalframes = inaudio.getnframes()

    frame = unpack('<hhhh', inaudio.readframes(2))
    end = frame[0] | (frame[1] << 8) | (frame[2] << 16) | (frame[3] << 24)
    dist = (totalframes / end) - 2

    bits = []
    for i in range(0, end, BUCKETS_TO_USE):
        frames = inaudio.readframes(CHUNK_SIZE)
        structsize = CHUNK_SIZE*2
        format = '<' + 'h'*structsize
        if not calcsize(format) == structsize:
            structsize *= 2
        chunk = unpack(format, frames)
        left = [ chunk[j] for j in range(0,len(chunk),2) ]
        right = [ chunk[j] for j in range(1,len(chunk),2) ]
        
        left_freqs = rfft(left)
        right_freqs = rfft(right)

        fbucket = len(left_freqs)/2 + 1
        for j in range(BUCKETS_TO_USE):
            bucket = fbucket + j*BUCKET_OFFSET
            bit = 0 if floor(left_freqs[bucket-1]) - floor(left_freqs[bucket]) <= 15 else 1
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

