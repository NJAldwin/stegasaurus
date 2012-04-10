#!/usr/bin/python
import os, sndhdr, subprocess

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

def convertmp3(filename):
    if not os.path.isfile(filename):
        raise IOError('File not found')

    basename = filename[:-4]
    inputname = filename
    outputname = basename + ".wav"

    print "Converting "+inputname+" to "+outputname+"..."

    subprocess.call([LAMEPATH, "--decode", inputname, outputname])


