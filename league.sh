#!/bin/bash

cd ~/league-scraper/
kill `cat pid`
source venv/bin/activate
python -W ignore league.py --logfile=log &
echo $! > pid
