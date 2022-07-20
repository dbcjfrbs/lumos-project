#!/bin/bash

# offset 가져오기
s=$(echo $MHA_LOG_GET_OFFSET)
e=$(ls -al /data/kakao1/ | wc -l)
cnt=$(expr $e - $s)

#업데이트 내역만 읽기
#ls -al /data/kakao1 | sed -n "$cnt, $ p"
ls -al /data/kakao1 | tail -n 3

#offset 업데이트
sed -i "10s/.*/export MHA_LOG_GET_CNT=$(ls -al /data/kakao1/ | wc -l)/g" .bashrc


