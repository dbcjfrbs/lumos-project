# offset 가져오기
s=$(echo $MHA_LOG_GET_CNT)
e=$(ls -al /data/kakao1/ | wc -l)
cnt=$(expr $e - $s)
#업데이트 내역만 읽기
#ls -al /data/kakao1 | sed -n "$cnt, $ p"
ls -al /data/kakao1 | tail -n 1
#offset 업데이트
sed -i "10s/.*/export MHA_LOG_GET_CNT=`ls -al /data/kakao1/ | wc -l`/g" .bashrc
#.bashrc 업데이트
source .bashrc

#한 줄로 만든 거
sed -i "10s/.*/export MHA_LOG_GET_CNT=40/g" .bashrc;source .bashrc;s=$(echo $MHA_LOG_GET_CNT);e=$(ls -al /data/kakao1/ | wc -l);cnt=$(expr $e - $s);ls -al /data/kakao1 | tail -n 1;sed -i "10s/.*/export MHA_LOG_GET_CNT=`ls -al /data/kakao1/ | wc -l`/g" .bashrc;source .bashrc
