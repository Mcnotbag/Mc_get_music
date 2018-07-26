#!/usr/bin/env python
# -*- coding:utf-8 -*-

import re
import json
import execjs
import datetime
from urllib.parse import urlencode
from util.TornadoBaseUtil import TornadoBaseHandler
from tornado import web, gen, httpclient, options
from Api.zepingguo.common.status_code import StatusError
from Api.zepingguo.common.func import try_helper, get_wrapper, url2req, SHORT_DEFAULT_PAGE_SIZE, \
    datetime2timestamp, RenderHosts, sort_by_datetime
from Api.zepingguo.common.ApiObj import new_comment_obj

get_comment_first_page_url = "http://m.ctrip.com/webapp/hotel/hoteldetail/dianping/ID.html?"
get_comment_first_page_param = {
    "fr": "detail",
    "atime": "20171228",
    "days": "1",
    "supportwebp": "false"
}

get_comment_first_page_headers = {
    "Host": "m.ctrip.com",
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:55.0) Gecko/20100101 Firefox/55.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Cookie": 'list_hotel_price={"traceid":"100004883-6a9a0314-9393-4662-834d-e34a9580d175","pageid":"228032","searchcandidate":{"bedtype":"","person":0},"timestamp":1514457139308,"minpriceroom":{"avgprice":458,"currency":"RMB","iscanreserve":1,"isshadow":1,"isusedcashback":1,"isusedcoupon":-1,"roomid":2536315}}; supportwebp=true; JSESSIONID=F158BA297B6C62F3051A2F16B3CB9BD3; GUID=09031179311990530434; _ga=GA1.2.2048679041.1508291219; _gid=GA1.2.633184397.1514457125; _gat=1; Union=OUID=&AllianceID=20640&SID=455414&SourceID=1572&Expires=1515061926909; ASP.NET_SessionSvc=MTAuMTUuMTI4LjI3fDkwOTB8b3V5YW5nfGRlZmF1bHR8MTUwOTk3MDkxODk5Mw; _bfa=1.1506421833139.zx6mb9.1.1506421833139.1514457147310.5.25.212094; page_time=1508291174586,1508291457751,1508292263258,1508292408822,1514457126776,1514457133400,1514457139732,1514457147945; _RF1={IP}; _RSG=CB4AIJoUZVB3m2NpmfjWDA; _RDG=28d8a3cef126ed28e9331c562b2abbe224; _RGUID=b7e37b24-d228-42cc-a360-b69c335c2c03; MKT_Pagesource=H5; _jzqco=|||||1.1364822876.1508291216286.1514457139875.1514457149314.1514457139875.1514457149314.0.0.0.8.8; Mkt_UnionRecord=[{"aid":"20640","timestamp":1514457149458}]',
    "Connection": "close",
    "Upgrade-Insecure-Requests": "1"
}

get_comment_url = "http://m.ctrip.com/restapi/soa2/10935/hotel/booking/commentgroupsearch"
get_comment_header = {
    "Host": "m.ctrip.com",
    "Connection": "close",
    "Referer": "",
    "Origin": "https://m.ctrip.com",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "x-ctrip-pageid": "228032",
    "User-Agent": "Mozilla/5.0 (Linux; U; Android 4.1.1; en-us; Google Nexus 7 - 4.1.1 - API 16 - "
                  "800x1280 Build/JRO03S) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Safari/534.30",
    "Accept-Language": "en-US",
    "Accept-Charset": "utf-8, iso-8859-1, utf-16, *;q=0.7",
    #"Cookie":
}

post_body = {
    "flag": 1,
    "id": "1053424",
    "htype": 1,
    "sort": {
        "idx": 2,
        "size": 10,
        "sort": 2,
        "ord": 1
    },
    "search": {
        "kword": "",
        "gtype": 4,
        "opr": 0,
        "ctrl": 14,
        "filters": []
    },
    "alliance": {
        "aid": "4897",
        "sid": "182042",
        "ouid": "",
        "ishybrid": 0},
    "Key": "",
    "head": {
        "cid": "09031011311681378794",
        "ctok": "",
        "cver": "1.0",
        "lang": "01",
        "sid": "497",
        "syscode": "09",
        "auth":None,
        "extension": [
            {"name":"pageid","value":"228032"},
            {"name":"webp","value":1},
            {"name":"referrer","value":""},
            {"name":"protocal","value":"https"}]},
    "contentType":"json"
}

get_token_url = "http://m.ctrip.com/webapp/hotel/j/hoteldetail/dianping/api/cas/gk/{ID}?cb=____casf{STEP}"
get_token_headers = {
    "Host": "m.ctrip.com",
    "User-Agent": "Mozilla/5.0 (Linux; U; Android 6.0; zh-cn; Redmi Note 4 Build/MRA58K) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/53.0.2785.146 Mobile Safari/537.36 XiaoMi/MiuiBrowser/9.3.10",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Referer": "",
    "X-Requested-With": "XMLHttpRequest",
    "Cookie": 'list_hotel_price={"traceid":"100004883-6a9a0314-9393-4662-834d-e34a9580d175","pageid":"228032","searchcandidate":{"bedtype":"","person":0},"timestamp":1514457139308,"minpriceroom":{"avgprice":458,"currency":"RMB","iscanreserve":1,"isshadow":1,"isusedcashback":1,"isusedcoupon":-1,"roomid":2536315}}; supportwebp=true; JSESSIONID=8CF492B18A0D4CE6E50038BFC7AA47AB; GUID=09031179311990530434; _ga=GA1.2.2048679041.1508291219; _gid=GA1.2.633184397.1514457125; Union=OUID=&AllianceID=20640&SID=455414&SourceID=1572&Expires=1515061926909; ASP.NET_SessionSvc=MTAuMTUuMTI4LjI3fDkwOTB8b3V5YW5nfGRlZmF1bHR8MTUwOTk3MDkxODk5Mw; _bfa=1.1506421833139.zx6mb9.1.1506421833139.1514457159035.5.26.228032; page_time=1508291174586,1508291457751,1508292263258,1508292408822,1514457126776,1514457133400,1514457139732,1514457147945,1514457159430; _RF1={IP}; _RSG=CB4AIJoUZVB3m2NpmfjWDA; _RDG=28d8a3cef126ed28e9331c562b2abbe224; _RGUID=b7e37b24-d228-42cc-a360-b69c335c2c03; MKT_Pagesource=H5; _jzqco=|||||1.1364822876.1508291216286.1514457149314.1514457159791.1514457149314.1514457159791.0.0.0.9.9; Mkt_UnionRecord=[{"aid":"20640","timestamp":1514457159868}]',
    "Connection": "close"
}

second_page_url = "http://m.ctrip.com/webapp/hotel/api/hotelcomment?"
second_page_param = {
    "hotelId": 450229,
    "pageSize": 10,
    "pageIndex": "2",
    "groupTypeBitMap": "2",
    "controlBitMap": "1",
    "showTag": 0,
    "sortType": 0,
    "recommendType": 0,
    "userTravelType": -1,
    "tagId": -1,
    "isFirstPage": 0,
    "atime": "20171228",
    "days": 1,
    # "key": "99538eecdc81c0326cd7464ba57ed734762f76fda12f4ef3274165defc620215"
}
second_page_headers = {
    "Host": "m.ctrip.com",
    "Origin": "http://m.ctrip.com",
    "User-Agent": "Mozilla/5.0 (Linux; U; Android 6.0; zh-cn; Redmi Note 4 Build/MRA58K) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/53.0.2785.146 Mobile Safari/537.36 XiaoMi/MiuiBrowser/9.3.10",
    "Accept": "text/html",
    "Accept-Language": "zh-CN,en-US;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Referer": "",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/json",
    "Cookie": 'list_hotel_price={"traceid":"100004883-6a9a0314-9393-4662-834d-e34a9580d175","pageid":"228032","searchcandidate":{"bedtype":"","person":0},"timestamp":1514457139308,"minpriceroom":{"avgprice":458,"currency":"RMB","iscanreserve":1,"isshadow":1,"isusedcashback":1,"isusedcoupon":-1,"roomid":2536315}}; supportwebp=true; JSESSIONID=F158BA297B6C62F3051A2F16B3CB9BD3; GUID=09031179311990530434; _ga=GA1.2.2048679041.1508291219; _gid=GA1.2.633184397.1514457125; _gat=1; Union=OUID=&AllianceID=20640&SID=455414&SourceID=1572&Expires=1515061926909; ASP.NET_SessionSvc=MTAuMTUuMTI4LjI3fDkwOTB8b3V5YW5nfGRlZmF1bHR8MTUwOTk3MDkxODk5Mw; _bfa=1.1506421833139.zx6mb9.1.1506421833139.1514457147310.5.25.212094; page_time=1508291174586,1508291457751,1508292263258,1508292408822,1514457126776,1514457133400,1514457139732,1514457147945; _RF1={IP}; _RSG=CB4AIJoUZVB3m2NpmfjWDA; _RDG=28d8a3cef126ed28e9331c562b2abbe224; _RGUID=b7e37b24-d228-42cc-a360-b69c335c2c03; MKT_Pagesource=H5; _jzqco=|||||1.1364822876.1508291216286.1514457139875.1514457149314.1514457139875.1514457149314.0.0.0.8.8; Mkt_UnionRecord=[{"aid":"20640","timestamp":1514457149458}]',
    "Connection": "close"
}

last_ts = None
header_faked = False
variables = [None]

opr_dict = {
    "0": u"全部",
    "1": u"推荐",
    "2": u"待改善",
    "3": u"有图"
}

sort_dict = {
    "0": "最热",
    "1": "最新"
}


class SearchHandler(TornadoBaseHandler):
    @get_wrapper(id="", parent="", pageToken="1", sort="1", size=SHORT_DEFAULT_PAGE_SIZE)  # Default parameters
    def get(self):
        pass

    @try_helper()
    @gen.coroutine  # for yield inside get_objects()
    def get_objects(self, adic):
        self.adic = adic  # adic is a dictionary of parameters
        self.async_client = httpclient.AsyncHTTPClient()
        start_req = yield self.get_start_req()
        response = yield self.async_client.fetch(start_req)
        self.parse_response(response)
        if int(self.adic["sort"]) == 1:
            self.item_list.sort(key=sort_by_datetime, reverse=True)
        result = {
            "data": self.item_list,
            "pageToken": self.pageToken,
            "hasNext": self.has_next
        }
        raise StatusError.Succeed(result)

    def fake_ctrip_header(self, header):
        if header["Cookie"]:
            header["Cookie"] = header["Cookie"].replace("{IP}", self.Variables.public_ip)

    def decode_token(self, html, href):
        def repl(result):
            variables[0] = result.group(1)
            return ""
        fake_js_obj = """
        function createElement(string) { return {body: "html"}; }
        this["require"] = undefined;
        document = {
                body: {"innerHTML" : "<html></html>"},
                referrer: undefined,
                documentElement: { "attributes": { "webdriver": undefined } },
                createElement: createElement
            };
            window = {
                Script: undefined,
                location: {
                    href: undefined
                },
                document: {"$cdc_asdjflasutopfhvcZLmcfl_": undefined },
                indexedDB: true,
                createElement: createElement
            };
            navigator = {
                userAgent: "%s",
                geolocation: true
            };
            location = {
                href: "%s"
            };
            window.location.href = location.href;
        """ % (get_token_headers["User-Agent"], href)
        rgx_function = re.compile("res\}\((\[.+?\]).+?String\.fromCharCode\(.+?(\d+)\)", re.DOTALL)
        r = re.search(rgx_function, html.decode("utf8"))
        arr = json.loads(r.group(1))
        distance = int(r.group(2))
        js_text = u""
        for i in arr:
            js_text += chr(i - distance)

        js_text = js_text.replace(";!function()", "function gensign()")
        js_text = fake_js_obj + re.sub("\s\S+new Function\(.+?\+\s(.+?)\s\+.+?\);", repl, js_text)
        js_text = js_text[:-4] + "return %s; }" % (variables[0],)
        js_text = js_text.replace("new Image()", 'a=1')
        sign = self.execjs(js_text, "gensign")
        if sign == u"老板给小三买了包， 却没有给你钱买房" or not sign.islower() or not sign.isalnum() or len(sign) != 64:
            raise StatusError.Token_overdue
        return sign

    @gen.coroutine
    def get_start_req(self):
        global header_faked
        if not header_faked:
            for header in (get_comment_first_page_headers, get_token_headers, second_page_headers):
                self.fake_ctrip_header(header)
                header_faked = True

        if not self.adic["id"] or self.adic["sort"] not in opr_dict:
            raise StatusError.Missing_param
        if self.adic["pageToken"] == "1" and self.adic["sort"] == "0":
            url = get_comment_first_page_url.replace("ID", self.adic["id"])
            get_comment_first_page_param["atime"] = datetime.datetime.now().strftime("%Y%m%d")
            req = url2req(url, "GET", headers=get_comment_first_page_headers)
        else:
            token_url = get_token_url.format(ID=0, STEP=self.adic["pageToken"])
            second_page_param["hotelId"] = int(self.adic["id"])
            second_page_param["pageSize"] = int(self.adic["size"])
            second_page_param["pageIndex"] = self.adic["pageToken"]
            second_page_param["sortType"] = int(self.adic["sort"])
            second_page_param["atime"] = datetime.datetime.now().strftime("%Y%m%d")
            second_page_param["isFirstPage"] = 1 if self.adic["pageToken"] == "1" else 0

            get_token_headers["Referer"] = "http://m.ctrip.com/webapp/hotel/hoteldetail/dianping/" + \
                                           self.adic["id"] + ".html?" + "fr=detail&atime=%s&days=1" % (second_page_param["atime"], )
            second_page_headers["Referer"] = get_token_headers["Referer"]

            token_req = url2req(token_url, "GET", get_token_headers)
            token_response = yield self.async_client.fetch(token_req)
            token = self.decode_token(token_response.body, get_comment_first_page_url.replace("ID", self.adic["id"]))
            # second_page_param["key"] = token
            url = second_page_url + urlencode({
                "pageid": "228032",
                "key": token
            })
            req = url2req(url, "POST", body=json.dumps(second_page_param), headers=second_page_headers)
        return req

    def parse_response(self, response):
        self.parse_html_response(response)

    def parse_html_response(self, response):
        str_body = response.body.decode("utf8")
        result1 = re.search('>(\{("|&#034;)hotelCommentCollectionRequest("|&#034;).+?\})<', str_body)
        result2 = re.search('(?<!<)(\{"hotelCommentCollectionRequest".+?\});', str_body)
        comments = list()
        if result1:
            json_obj = json.loads(self.FunctionUtil.ncr2unicode(result1.group(1)))
            if json_obj["hotelCommentCollectionResponse"]["groups"][0]["commentList"]:
                comments.extend(json_obj["hotelCommentCollectionResponse"]["groups"][0]["commentList"])
        if result2:
            json_obj = json.loads(result2.group(1))
            if json_obj["hotelCommentCollectionResponse"]["groups"][0]["commentList"]:
                comments.extend(json_obj["hotelCommentCollectionResponse"]["groups"][0]["commentList"])
        if not comments:
            raise StatusError.Succeed.EmptyResult
        self.item_list = list()
        comment_set = set()
        for comment in comments:
            if comment["commentId"] in comment_set:
                continue
            item = self.ApiObject.new_comment_obj()
            item["id"] = str(comment["commentId"])
            item["subobjects"] = [{
                "id": str(comment["basicRoomId"]),
                "name": comment["basicRoomName"]
            }]
            item["checkinDate"] = comment["checkInDate"]
            item["content"] = comment["commentContent"].replace("&lt;", "").replace("br/", "").replace("&gt;", "")
            item["commenterIdGrade"] = comment["commentGrade"]
            item["source"] = comment["commentSource"]
            if comment["hasFeedbacks"]:
                item["replies"] = list()
                for reply in comment["feedbacks"]:
                    item["replies"].append(
                        {
                            "name": reply["displayName"],
                            "date": None,
                            "content": reply["content"],
                            "id": None
                        }
                    )
            else:
                item["replies"] = None
            item["referId"] = str(comment["hotelId"])
            if comment["images"]:
                item["imageUrls"] = ["http://images4.c-ctrip.com/target/%s_W_640_640_Q50.jpg" %
                                     (each["imageUrl"]) for each in comment["images"]]
            else:
                item["imageUrls"] = None
            item["publishDate"] = datetime2timestamp(comment["postDate"] + " 00:00:00")
            item["rating"] = comment["ratingPoint"]
            item["commenterType"] = comment["travelTypeName"]
            item["commenterScreenName"] = comment["userNickName"]
            item["commenterGradeName"] = comment["userCommentGradeName"]
            item["url"] = "http://m.ctrip.com/webapp/hotel/hoteldetail/dianping/" + self.adic["id"] + ".html"
            comment_set.add(comment["commentId"])
            self.item_list.append(item)
        if json_obj["hotelCommentCollectionResponse"]["groups"][0]["totalPageCount"] >= int(self.adic["pageToken"]):
            self.has_next, self.pageToken = True, str(int(self.adic["pageToken"]) + 1)
        else:
            self.has_next, self.pageToken = False, None

    def parse_web_response(self, response):
        json_obj = json.loads(response.body)
        if not json_obj["groups"]:
            global last_ts
            last_ts = None
            raise StatusError.Succeed.EmptyResult
        comments = json_obj["groups"][0]["comments"]
        self.item_list = list()
        for each_comment in comments:
            item = new_comment_obj()
            item["id"] = str(each_comment["comid"])
            item["referId"] = str(each_comment["hid"])
            item["commenterId"] = each_comment["oid"]
            item["commenterScreenName"] = each_comment["nick"]
            item["publishDate"] = datetime2timestamp(each_comment["date"])
            item["content"] = each_comment["text"]
            if each_comment["imgs"]:
                item["imageUrls"] = list()
                for i in each_comment["imgs"]:
                    for each in i["items"]:
                        if "http" in each["url"]:
                            item["imageUrls"].append(each["url"])
                item["imageUrls"] = list(set(item["imageUrls"]))
            item["url"] = "http://m.ctrip.com/webapp/hotel/hoteldetail/dianping/" + self.adic["id"] + ".html"
            item["rating"] = float(each_comment["rats"]["all"])
            item["servRating"] = float(each_comment["rats"]["serv"])
            item["enviRating"] = float(each_comment["rats"]["arnd"])
            item["infraRating"] = float(each_comment["rats"]["facl"])
            item["hygieneRating"] = float(each_comment["rats"]["room"])
            item["replies"] = list()
            for reply in each_comment["rplist"]:
                item["replies"].append(
                    {
                        "name": reply["name"],
                        "date": reply["date"],
                        "content": reply["text"],
                        "id": None
                    }
                )
            item["likeCount"] = each_comment["uflcount"]
            item["commenterIdGrade"] = each_comment["star"]
            item["subobjectName"] = each_comment["rname"]
            item["subobjectId"] = str(each_comment["rid"])
            item["commenterType"] = each_comment["travel"]

            self.item_list.append(item)
        if json_obj["groups"][0]["idx"] < json_obj["groups"][0]["pages"]:
            self.has_next, self.pageToken = True, str(json_obj["groups"][0]["idx"] + 1)
        else:
            self.has_next, self.pageToken = False, None
