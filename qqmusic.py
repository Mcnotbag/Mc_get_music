import requests
import re
from datetime import datetime
import math
import random


# 歌曲songmid
# songmid = "000Md1wq0vnwzE"  # 体面
# songmid = "003vUjJp3QwFcd"  # 说散就散
#songmid = "0001ytd137SgJU" # 远大前程
# songmid = "001zxfZR1qu3ZQ"
# songmid = "001J5QJL1pRQYB" # 等你下课
songmid = "003tlSye3PpqAg"
filename = "C400{}.m4a".format(songmid)


# 获得songmid
# https://c.y.qq.com/v8/fcg-bin/fcg_v8_album_info_cp.fcg?albummid=001qYTzY2oyDyZ&platform=yqq
# # 获得文件名filename
# https://c.y.qq.com/v8/fcg-bin/fcg_v8_album_info_cp.fcg?albummid=001qYTzY2oyDyZ&platform=yqq

# 获取歌曲的guid
t = datetime.utcnow().microsecond // 1000
guid = math.trunc(2147483647 * random.random()) * t % 10000000000
cookies = {
    "pgv_pvid": str(guid),
}
cookie = "pgv_pvi=3962760192; pgv_si=s8593839104; pgv_info=ssid=s5461457355; pgv_pvid=3904984604; ts_uid=6149880823; _qpsvr_localtk=0.9352821208932514; yq_index=0; player_exist=1; qqmusic_fromtag=66; yqq_stat=0; ptisp=ctc; ptui_loginuin=332342731; pt2gguin=o0332342731; uin=o0332342731; skey=@ysRvMUuDo; RK=3d7IX9PUS2; ptcz=425e8d63f5f9a853467c0fc4e882817bd2140f7fd2f667289b30cfb61ea7e34c; luin=o0332342731; lskey=000100001dd6e648d58d25bed278aaae8845af6bf44a868066447ff43e4e65f6d6e8e0e1f943a4b8f766976c; p_uin=o0332342731; pt4_token=qIA5MWWDzEAuJB0PTzPYHlzFRj0-KQ89hBosRL9gc0s_; p_skey=uwocSSxd*Z2ZeraV0REGU7rfNNMz3IBUpkpHejBiQCw_; p_luin=o0332342731; p_lskey=00040000959bc83e6ea3321e3cf1b3d9cba87a3ff989c86e1db983afb9ca6ad82caef1577f6beb84beb9531a; ts_refer=xui.ptlogin2.qq.com/cgi-bin/xlogin; ts_last=y.qq.com/n/yqq/song/003tlSye3PpqAg.html; yplayer_open=1"
cookie = {i.split("=")[0]:i.split("=")[1] for i in cookie.split("; ")}
print(cookie)
# return _guid = Math.round(2147483647 * Math.random()) * t % 1e10,
# document.cookie = "pgv_pvid=" + _guid + "; Expires=Sun, 18 Jan 2038 00:00:00 GMT; PATH=/; DOMAIN=qq.com;", _guid

# 获得cid
# 向 https://y.gtimg.cn/music/portal/js/common/map.js 发送请求
# 获取"p1:"后的url的值
# 向获得的url地址发送请求
# 使用正则获得cid

map_url = "https://y.gtimg.cn/music/portal/js/common/map.js"
response = requests.get(map_url)
# with open("map.js", "w", encoding="utf-8") as f:
#     f.write(response.content.decode())

res_str = response.content.decode()

p1_url = re.findall(r'"p1":{"url":"(.*?)","deps"', res_str)
#print(p1_url)
if len(p1_url) > 0:
    p1_url = "https:" + p1_url[0]
    response = requests.get(p1_url)
    # with open("p1.js", "w", encoding="utf-8") as f:
    #     f.write(response.content.decode())
    res_str = response.content.decode()

    cid = re.findall(r"data:{cid:(\d*?),format", res_str)
    #print(cid)
    if len(cid) > 0:
        cid = cid[0]

else:
    print("p1_url为None")

#
# 获取歌曲的vkey
vkey_url = "https://c.y.qq.com/base/fcgi-bin/fcg_music_express_mobile3.fcg?&platform=yqq&cid={}&songmid={}&filename={}&guid={}"
vkey_url = vkey_url.format(cid, songmid, filename, guid)


response = requests.get(vkey_url, cookies=cookie)
with open("vkey.fcg", "w", encoding="utf-8") as f:
    f.write(response.content.decode())

res_str = response.content.decode()

vkey = re.findall(r'"vkey":"(.*?)"', res_str)
vkey = vkey[0]

# # 获取歌曲
# http://dl.stream.qqmusic.qq.com/C400000Md1wq0vnwzE.m4a?vkey=4A1B7F433D22D99BF221BAF429EDD4B73D3BCE90C5006C97B9A7B68CE792E61B2AB1C7C66E53C9F2963E6DCA85F82A10FF3CEED7C450D711&guid=4422592355
song_url = "http://dl.stream.qqmusic.qq.com/{}?vkey={}&guid={}&uin=0&fromtag=6"

song_url = song_url.format(filename, vkey, guid)
print(song_url)

res = requests.get(song_url, cookies=cookies)
with open(filename, "wb") as f:
    f.write(res.content)


#
# guid
# var t = (new Date).getUTCMilliseconds();
#         return _guid = Math.round(2147483647 * Math.random()) * t % 1e10,
#         document.cookie = "pgv_pvid=" + _guid + "; Expires=Sun, 18 Jan 2038 00:00:00 GMT; PATH=/; DOMAIN=qq.com;",
#         _guid
# # 通过计算得到
# # 设置cookie
#
# # 向这个地址发请求可以获得player_module_2e0875c.js的地址
# map.js
#
# # 通过这个地址可以获得cid
# player_module_2e0875c.js
#
#
# #
# cid # player_module_2e0875c.js 中有 通过map.js可以获得player_module_2e0875c.js的地址
#
# songmid # 每首都有的
#
# filename # vkey的地址中有
#
# guid
#
#
# 这个地址可以返回一个vkey
# https://c.y.qq.com/base/fcgi-bin/fcg_music_express_mobile3.fcg?platform=yqq&cid=205361747&songmid=001J5QJL1pRQYB&filename=C400001J5QJL1pRQYB.m4a&guid=3427487936
# #
# vkey # vkey的地址中有
#
# guid
#
# filename  # vkey的地址中有
#
#
# http://dl.stream.qqmusic.qq.com/C400001J5QJL1pRQYB.m4a?vkey=&guid=3427487936&uin=0&fromtag=66