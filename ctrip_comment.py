import re
import time
import random
import string
import json
import execjs
from datetime import datetime
from tornado import gen, httpclient
from util.TornadoBaseUtil import TornadoBaseHandler
from Api.zepingguo.api.hotel.ctrip import hotel_detail_headers

get_token_url = "http://m.ctrip.com/restapi/soa2/10934/hotel/customer/cas?_fxpcqlniredt="  # guuid
get_token_headers = {
    "Host": "m.ctrip.com",
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:56.0) Gecko/20100101 Firefox/56.0",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Referer": "http://m.ctrip.com/webapp/hotel/hoteldetail/dianping/5860925.html",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/json",
    "Cookie": "ASP.NET_SessionId=dno4iufil4hepsgolbseekag; _bfa=1.1509700598966.7p7ubv.1.1509700598966.1509700650052.1.11.228032; page_time=1509700600627%2C1509700603250; GUID=09031014210846161441; _abtest_userid=d8e5d589-0367-4e6c-8272-9fe263d31d8a; _RF1={IP}; _RSG=QsqRt5ylnI3TVvmvwKPILB; _RDG=285bf10a1483aa27bf252e85f9a02459fa; _RGUID=34b1bfc1-776f-4d9a-b552-654eb9c397dd; _jzqco=%7C%7C%7C%7C%7C1.1819574141.1509700604622.1509700604622.1509700604623.1509700604622.1509700604623.0.0.0.1.1; _ga=GA1.2.964392904.1509700605; _gid=GA1.2.791572248.1509700605; _gat=1",
    "Connection": "close",
    "x-ctrip-pageid": "228032"
}

get_token_body = {
    "callback": "TeEObITYmiShXmHjN",
    "alliance": {
        "ishybrid": 0
    },
    "head": {
        "cid": "09031014210846161441",
        "ctok": "",
        "cver": "1.0",
        "lang": "01",
        "sid": "8888",
        "syscode": "09",
        "auth": None,
        "extension": [
            {"name": "pageid", "value": "228032"},
            {"name": "webp", "value": 0},
            {"name": "referrer", "value": "http://m.ctrip.com/html5/"},
            {"name": "protocal", "value": "http"}]},
    "contentType": "json"
}

get_content_url = "http://m.ctrip.com/restapi/soa2/10935/hotel/booking/commentgroupsearch?_fxpcqlniredt=" # guuid
get_content_headers = get_token_headers
get_content_param = {"flag": 1,
                     "id": "5860925",
                     "htype": 1,
                     "sort": {"idx":1,"size":10,"sort":2,"ord":1},
                     "search":{"kword":"","gtype":4,"opr":0,"ctrl":14,"filters":[]},
                     "alliance":{"ishybrid":0},
                     "Key":"c2cb2ba68aa4138dab7799ebd05a2b14487b5df876cfa0e4f053e928d07c3210",
                     "head":{"cid":"09031014210846161441","ctok":"","cver":"1.0","lang":"01","sid":"8888",
                             "syscode":"09","auth":None,"extension":
                                 [{"name":"pageid","value":"228032"},
                                  {"name":"webp","value":0},
                                  {"name":"referrer","value":"http://m.ctrip.com/html5/"},
                                  {"name":"protocal","value":"http"}]},"contentType":"json"}

DEFAULT_PAGE_SIZE = TornadoBaseHandler.CommonUtil.DEFAULT_PAGE_SIZE
global_pageid = None
global_prev_ts = None
global_guuid = None
global_token = None
global_prev_fetch_id = None
variables = [None]


class SearchHandler(TornadoBaseHandler):
    def robust_get(self, id="", pageToken="1", sort="1", size=DEFAULT_PAGE_SIZE):
        start_req = yield self.get_start_req()
        try:
            response = yield self.async_client.fetch(start_req)
        except httpclient.HTTPError as e:
            if e.code == 432:
                yield self.fetch_and_refresh_guuid()
                start_req = yield self.get_start_req()
                response = yield self.async_client.fetch(start_req)
        self.parse_response(response)
        result = ({
            "data": self.item_list,
            "pageToken": self.page_token,
            "hasNext": self.has_next
        })
        raise self.StatusError.Succeed(result)

    @gen.coroutine
    def get_start_req(self):
        global global_guuid, global_token, global_pageid
        if not self.adic["id"] or not self.adic["pageToken"].isdigit():
            raise self.StatusError.Missing_param
        if not global_guuid:
            yield self.fetch_and_refresh_guuid()

        get_content_param["id"] = self.adic["id"]
        get_content_param["sort"]["idx"] = int(self.adic["pageToken"])
        get_content_param["sort"]["size"] = int(self.adic["size"])
        get_content_param["sort"]["size"] = int(self.adic["sort"])
        yield self.get_token(get_content_headers["Referer"])
        self.update_param()
        url = get_content_url + global_guuid
        req = self.CommonUtil.url2req(url, "POST", body=json.dumps(get_content_param), headers=get_content_headers)
        return req

    def update_param(self):
        get_content_param["Key"] = global_token
        get_content_param["head"]["cid"] = global_guuid
        get_content_param["head"]["extension"][0]["value"] = global_pageid

    @gen.coroutine
    def get_token(self, href, force=False):
        global global_pageid, global_prev_ts, global_guuid, global_prev_fetch_id, global_token
        ts = time.time()
        if not force or not global_prev_ts or ts - global_prev_ts > 60:
            self.logging.info("Fetching new token")
            url = get_token_url + global_guuid
            get_token_body["callback"] = "".join(random.choice(string.ascii_lowercase + string.ascii_uppercase)
                                                 for _ in range(17))
            get_token_body["head"]["cid"] = global_guuid

            global_pageid = get_token_body["head"]["extension"][0]["value"] = str(random.randint(100000, 999999))
            req = self.CommonUtil.url2req(url, "POST", body=json.dumps(get_token_body),
                                          headers=get_token_headers)
            response = yield self.async_client.fetch(req)
            global_token = self.decode_token(response.body.decode("utf8"), href)
            global_prev_ts = ts
        return global_token

    @gen.coroutine
    def fetch_and_refresh_guuid(self):
        global global_guuid
        url = "http://m.ctrip.com/webapp/hotel/hoteldetail/457399.html?days=1&atime=" + datetime.now().strftime("%Y%m%d")
        if "Cookie" in hotel_detail_headers:
            del hotel_detail_headers["Cookie"]
        req = self.CommonUtil.url2req(url, "GET", headers=hotel_detail_headers)
        response = yield self.async_client.fetch(req)
        for header, v in response.headers.get_all():
            if header == "Set-Cookie":
                if "GUID=" in v:
                    global_guuid = v.split(";")[0].split("=")[1]
                if "JSESSIONID" in v:
                    jsession = v.split(";")[0].split("=")[1]

        for header in get_token_headers, get_content_headers:  # room_headers:
            header["Cookie"] = re.sub("[\s|^]GUID=(\d+)", " GUID=" + global_guuid, header["Cookie"])

    def parse_response(self, response):
        json_obj = json.loads(response.body)
        if not json_obj["groups"]:
            raise self.StatusError.Succeed.EmptyResult
        comments = json_obj["groups"][0]["comments"]
        self.item_list = list()
        for comment in comments:
            item = self.ApiObject.new_comment_obj()
            item["id"] = str(comment["comid"])
            item["subobjects"] = [{
                "id": str(comment["oid"]),
                "name": comment["rname"]
            }]
            item["checkinDate"] = comment["cdate"]
            item["content"] = comment["text"]
            item["commenterIdGrade"] = comment["userinfo"]["star"]
            item["source"] = str(comment["source"])
            if comment["rplist"]:
                item["replies"] = list()
                for reply in comment["rplist"]:
                    item["replies"].append(
                        {
                            "name": reply["name"],
                            "date": reply["date"],
                            "content": reply["text"],
                            "id": str(reply["cid"])
                        }
                    )
            else:
                item["replies"] = None
            item["referId"] = str(comment["hid"])
            if comment["imgs"]:
                item["imageUrls"] = set()
                for all_imgs in comment["imgs"]:
                    for each in all_imgs["items"]:
                        if "http" in each["url"]:
                            item["imageUrls"].add(each["url"])
                        else:
                            item["imageUrls"].add("http://images4.c-ctrip.com/target/%s_W_640_640_Q50.jpg" % (each["url"], ))
                item["imageUrls"] = list(item["imageUrls"])
            else:
                item["imageUrls"] = None
            item["publishDate"] = self.FunctionUtil.datetime2timestamp(comment["date"])
            item["rating"] = comment["rats"]["all"]
            item["commenterScreenName"] = comment["userinfo"]["nick"]
            item["url"] = "http://m.ctrip.com/webapp/hotel/hoteldetail/dianping/" + self.adic["id"] + ".html"
            item["qualRating"] = comment["rats"]["room"]
            item["enviRating"] = comment["rats"]["arnd"]
            item["servRating"] = comment["rats"]["serv"]
            item["infraRating"] = comment["rats"]["facl"]
            self.item_list.append(item)
        if json_obj["groups"][0]["pages"] >= int(self.adic["pageToken"]):
            self.has_next, self.page_token = True, str(int(self.adic["pageToken"]) + 1)
        else:
            self.has_next, self.page_token = False, None

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
        """ % (get_content_headers["User-Agent"], href)
        rgx_function = re.compile("res\}\((\[.+?\]).+?String\.fromCharCode\(.+?(\d+)\)", re.DOTALL)
        r = re.search(rgx_function, html)
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
            with open("ctrip_html", "w") as f:
                f.write(html)
            raise self.StatusError.Token_overdue
        return sign
