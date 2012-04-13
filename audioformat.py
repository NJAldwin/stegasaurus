#!/usr/bin/python
import os, sndhdr, subprocess

# FIXME: Make sure this path reflects the machine you're testing on
# This isn't used anywhere at the moment...
#LAMEPATH = "/course/cs4500wc/Lame/src/lame-3.98.4/frontend/lame" # Path to LAME executable
LAMEPATH = "/usr/local/bin/lame" # Path to LAME executable

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
    subprocess.call([LAMEPATH, to_wav, inputname, outputname])

    return outputname
