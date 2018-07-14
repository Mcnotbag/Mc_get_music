
import requests
import Music


first1 = '{"ids":"[499008025]","br":128000,"csrf_token":""}'

first2 = '{"logs":"[{\"action\":\"activeweb\",\"json\":{\"is_organic\":0,\"url\":\"https://music.163.com/#/search/m/?id=2116&s=%E9%99%88%E5%A5%95%E8%BF%85-%E4%BB%BB%E6%88%91%E8%A1%8C&type=1\",\"source\":\"https://www.baidu.com/link?url=-BJoWJaVofxO7h5dfkfj_PH052P_QzZv3Z3GtYa7c1K&wd=&eqid=a1ba6e6e00024eb3000000065b497b83\"}}]","csrf_token":""}'

first3 = '{"logs":"[{\"action\":\"searchkeywordclient\",\"json\":{\"type\":\"song\",\"keyword\":\"陈奕迅-任我行\",\"offset\":0}}]","csrf_token":""}'

first4 = '{"hlpretag":"<span class=\"s-fc7\">","hlposttag":"</span>","id":"2116","s":"陈奕迅-任我行","type":"1","offset":"0","total":"true","limit":"30","csrf_token":""}'

first5 = '{"s":"陈奕迅-任我行","csrf_token":""}'

# 播放音乐

first_1 = '{"id":"27483202","c":"[{\"id\":\"27483202\"}]","csrf_token":""}'

first_2 = '{"ids":"[27483202]","br":128000,"csrf_token":""}'

first_3 = '{"logs":"[{\"action\":\"play\",\"json\":{\"id\":\"27483202\",\"type\":\"song\",\"source\":\"search\",\"sourceid\":\"陈奕迅-任我行\"}}]","csrf_token":""}'

obj = Music.WangYiYun()
text = obj.create_random_16()
params = obj.get_params(text,first1)
encsecKey = obj.get_encSEcKey(text)
data = {
    "params":params,
    "encSecKey":encsecKey
}

url = "https://music.163.com/weapi/song/enhance/player/url?csrf_token="
headers = {
    "Referer":"https://music.163.com/",
    "Host":"music.163.com",
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36"
}
response = requests.post(url,data=data,headers=headers)
print(response.content.decode())


#
# response_m = requests.get("http://m10.music.126.net/20180714181904/bcd616be5f092b8fa0e7960355ce6201/ymusic/70f8/53e6/64c6/95588d90b0e309108c64faa58892c23e.mp3")
# print(response_m.content)