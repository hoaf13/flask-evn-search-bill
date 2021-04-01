#!/bin/sh
 
python3 run.py &
python3 app/components/boost_intent.py &
python3 app/components/boost_intent.py &
python3 app/components/boost_entity.py &
python3 app/components/boost_entity.py &&
killall python3
