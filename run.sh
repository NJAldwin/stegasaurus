#!/usr/bin/env bash

PAYLOAD=$1
INPUT=$2
OUTPUT=$3
PAYOUT=$4

if [ -z "$INPUT" ]
then
     INPUT="Hewlett.wav"
fi

if [ -z "$PAYLOAD" ]
then
     PAYLOAD="stegan"
fi

if [ -z "$OUTPUT" ]
then
     OUTPUT="output.wav"
fi

if [ -z "$PAYOUT" ]
then
     PAYOUT="output.txt"
fi

echo "./stegan --encode $INPUT $PAYLOAD $OUTPUT"
./stegan --encode $INPUT $PAYLOAD $OUTPUT
echo "./stegan --decode $OUTPUT $PAYOUT"
./stegan --decode $OUTPUT $PAYOUT
echo "diff $PAYLOAD $PAYOUT"
DIFFOUT=`diff $PAYLOAD $PAYOUT`
if [ -z "$DIFFOUT" ]
then
     echo "The files are the same"
else
     echo $DIFFOUT
fi
