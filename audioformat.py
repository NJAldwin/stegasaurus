#!/usr/bin/python
import os, sndhdr, subprocess

LAMEPATH = "/course/cs4500wc/Lame/src/lame-3.98.4/frontend/lame" # CCIS path to LAME executable
#LAMEPATH = "/usr/bin/lame" # Local path to LAME executable

def checkformat(filename, expectedtype, expectedrate):
    """ Check that the file is in the expected format """
    if not os.path.isfile(filename):
        return False

    header = sndhdr.what(filename)
    # later: mp3 checking
    if header == None:
        return False

    ftype, rate, channels, frames, bps = header
    return ftype==expectedtype and rate==expectedrate

def convertformat(filename,fmt):
    if not os.path.isfile(filename):
        raise IOError('File not found')

    basename = filename[:-len(fmt)]
    inputname = filename
    outputname = basename + fmt

    print "Converting "+inputname+" to "+outputname+"..."

    to_wav = '--decode' if fmt == 'wav' else ''
    subprocess.call([LAMEPATH, to_wav, '-q 9', '--quiet', inputname, outputname])

    return outputname
