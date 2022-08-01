# offset 가져오기
s=$(echo $MHA_LOG_GET_CNT)
e=$(ls -al /data/kakao1/ | wc -l)
cnt=$(expr $e - $s)
#업데이트 내역만 읽기
#ls -al /data/kakao1 | sed -n "$cnt, $ p" : 파기함
ls -al /data/kakao1 | tail -n 1
#offset 업데이트
sed -i "10s/.*/export MHA_LOG_GET_CNT=`ls -al /data/kakao1/ | wc -l`/g" .bashrc
#.bashrc 업데이트
source .bashrc

#한 줄로 만든 거
sed -i "10s/.*/export MHA_LOG_GET_CNT=40/g" .bashrc;source .bashrc;s=$(echo $MHA_LOG_GET_CNT);e=$(ls -al /data/kakao1/ | wc -l);cnt=$(expr $e - $s);ls -al /data/kakao1 | tail -n 1;sed -i "10s/.*/export MHA_LOG_GET_CNT=`ls -al /data/kakao1/ | wc -l`/g" .bashrc;source .bashrc


########### 회의 피드백 : offset 설정 로직 다시짤 것 ############## : 파기함
# offset 가져오기
ls -a | grep {new_offset_point}
"ls -a /data/* | grep {new_offset_point}"
"s=$(echo $MHA_LOG_GET_CNT);e=$(ls -a /data/kakao1/ | wc -l);cnt=$(expr $e - $s);ls -a /data/kakao1 | tail -n $cnt;sed -i \"10s/.*/export MHA_LOG_GET_CNT=`ls -a /data/kakao1/ | wc -l`/g\" .bashrc;source .bashrc;"

#date로 받아가지고 그것보다 큰 거 출력
"ls -a /data/* | awk -F '.' '{print $4}' | awk -F '_' '{print $1}' | awk '$1 > {last_offset_point}'"


file_cnt=$(ls -al /data/* | grep ^- | awk '{print $9}' | wc -l);cnt=1;while [ ${cnt} -le ${file_cnt} ];do file_=$(ls -al /data/* | grep ^- | awk '{print $9}' | head -$cnt | tail -1);file_path=$(sudo find /data -name $file_);started_at=$(cat $file_path | head -1);echo $started_at | cut -d ' ' -f 1-5;cnt=$((cnt+1));done



# ims 정보 얻는 방법
# curl -X GET 'http://api.ims.daumkakao.io/v1/serverViews?hostname=replica-master';

# def get_ims_info_by_host_name(host_name):
#     url = 'http://api.ims.daumkakao.io/v1/serverViews?hostname='+str(host_name)
#     try:
#         res = requests.get(url=url)
#         return res
#     except Exception as e:
#         print(e)
		
# "zone_name":"ay_dev_vm", - zone정보
# "loc_b":"AY1" -IDC 정보

