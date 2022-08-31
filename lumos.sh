#!/bin/bash

source ~/.bash_profile
pushd /home/deploy/lumos > /dev/null
python batch.py >> lumos_batch.log
popd > /dev/null