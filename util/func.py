import requests
### ims 정보 가져오기
def get_ims_info_by_host_name(host_name):
    url = 'http://api.ims.daumkakao.io/v1/serverViews?hostname='+str(host_name)
    try:
        res = requests.get(url=url)
        return res
    except Exception as e:
        print(e)
