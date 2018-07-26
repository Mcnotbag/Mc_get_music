#!/usr/bin/env python
# -*- coding:utf-8 -*-

import json
import time
from util.TornadoBaseUtil import TornadoBaseHandler
import logging
from tornado import web, gen, httpclient, options
from Api.zepingguo.common.status_code import StatusError
from Api.zepingguo.common.func import try_helper, get_wrapper, url2req, \
    DEFAULT_PAGE_SIZE, SHORT_DEFAULT_PAGE_SIZE
from Api.zepingguo.common.ApiObj import new_comment_obj
from urllib.parse import urlencode
from Api.zepingguo.api.post.ctrip import headers, get_timestamp

sight_comment_url = "https://m.ctrip.com/restapi/soa2/10491/json/GetCommentListAndHotTagList"
post_comment_url = "https://m.ctrip.com/restapi/soa2/10129/json/GetTravelReplyListByUid"

sight_comment_param = {
    "CommentResultInfoEntity": {
        "BusinessId": "2778",
        "BusinessType": "11",
        "PoiId": 0,
        "PageIndex": 1,
        "PageSize": DEFAULT_PAGE_SIZE,
        "TouristType": 0,
        "SortType": 3,
        "ImageFilter": False,
        "StarType": 0,
        "CommentTagId": 0
    },
    "head": {
        "cid": "12001111510029361046",
        "ctok": "",
        "cver": "702.003",
        "lang": "01",
        "sid": "8890",
        "syscode": "12",
        "auth": None,
        "extension": [{"name": "protocal","value": "file"}]},
    "contentType": "json"
}

post_comment_param = {
    "Id": "2638847",
    "PageSize": DEFAULT_PAGE_SIZE,
    "PageIndex": 1,
    "head": {
        "cid": "12001111510029361046",
        "ctok": "",
        "cver": "702.003",
        "lang": "01",
        "sid": "8890",
        "syscode": "12",
        "auth": None,
        "extension": [{"name": "protocal", "value": "file"}]},
    "contentType": "json"
}

parents = ("sight", "post", "hotel")

sort_dict = {
    "0": "酒店最热",
    "1": "酒店最新",
    "2": "景点最热",
    "3": "景点最新"
}


class SearchHandler(TornadoBaseHandler):
    @get_wrapper(id="", parent="", pageToken="1", sort="1", size=DEFAULT_PAGE_SIZE)  # Default parameters
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
        result = {
            "data": self.item_list,
            "pageToken": self.pageToken,
            "hasNext": self.has_next
        }
        raise StatusError.Succeed(result)

    @gen.coroutine
    def get_start_req(self):
        if not self.adic["id"] or self.adic["parent"] not in parents:
            raise StatusError.Missing_param
        if self.adic["parent"] == "hotel":
            if self.adic["size"] == str(DEFAULT_PAGE_SIZE):
                self.adic["size"] = SHORT_DEFAULT_PAGE_SIZE
            req = url2req("http://localhost:" + str(options.options.port) + "/comment/ctripHotel?" + urlencode(self.adic))
            response = yield self.async_client.fetch(req, raise_error=False)
            raise StatusError.Succeed(json.loads(response.body))

        if self.adic["parent"] == "sight":
            if self.adic["sort"] == "1":
                self.adic["sort"] = "3"
            elif self.adic["sort"] not in sort_dict:
                raise self.StatusError.Missing_param
            sight_comment_param["CommentResultInfoEntity"]["BusinessId"] = self.adic["id"]
            sight_comment_param["CommentResultInfoEntity"]["PageIndex"] = int(self.adic["pageToken"])
            sight_comment_param["CommentResultInfoEntity"]["PageSize"] = int(self.adic["size"])
            sight_comment_param["CommentResultInfoEntity"]["SortType"] = int(self.adic["sort"])
            if sight_comment_param["CommentResultInfoEntity"]["SortType"] == 3:
                sight_comment_param["CommentResultInfoEntity"]["CommentTagId"] = -1
            # logging.info(sight_comment_url)
            req = url2req(sight_comment_url, "POST", headers, body=json.dumps(sight_comment_param))
        else:
            post_comment_param["Id"] = self.adic["id"]
            post_comment_param["PageSize"] = int(self.adic["size"])
            post_comment_param["PageIndex"] = int(self.adic["pageToken"])
            # logging.info(post_comment_url)
            req = url2req(post_comment_url, "POST", headers, body=json.dumps(post_comment_param))
        return req

    def parse_response(self, response):
        self.item_list = list()
        json_obj = json.loads(response.body)
        if self.adic["parent"] == "sight":
            self.parse_sight_response(json_obj)
        else:
            self.parse_post_response(json_obj)

    def parse_sight_response(self, json_obj):
        comment_result = json_obj["CommentResult"]
        info = comment_result["CommentInfo"]
        if not info:
            raise StatusError.Succeed.EmptyResult
        now_ts = int(time.time())
        for each_item in info:
            item = new_comment_obj()
            item["id"] = str(each_item["CommentId"])
            item["referId"] = str(each_item["ResourceId"])
            item["commenterId"] = str(each_item["UserId"])
            item["commenterScreenName"] = each_item["UserInfoModel"]["UserNick"] \
                if "UserNick" in each_item["UserInfoModel"] and each_item["UserInfoModel"]["UserNick"] else None
            item["publishDate"] = get_timestamp(each_item["PublishTime"])
            if item["publishDate"] > now_ts:
                continue
            item["content"] = each_item["Content"]
            item["rating"] = each_item["TotalStar"]
            item["imageUrls"] = [i["PhotoPath"] for i in each_item["Images"]]
            if not item["imageUrls"]:
                item["imageUrls"] = None
            item["url"] = "https://m.ctrip.com/webapp/you/comment/detail/2778/11/" + item["id"] + ".html"
            item["likeCount"] = each_item["UsefulCount"]
            if "PlatformVersion" in each_item:
                item["source"] = each_item["PlatformVersion"]
            item["ip"] = each_item["IP"] if "IP" in each_item and each_item["IP"] else None
            item["commenterIdGrade"] = str(each_item["UserInfoModel"]["UserVIPLevel"])
            self.item_list.append(item)
        if int(self.adic["size"]) * (int(self.adic["pageToken"]) - 1) + len(self.item_list) < comment_result["TotalCount"]:
            self.has_next, self.pageToken = True, str(int(self.adic["pageToken"]) + 1)
        else:
            self.has_next, self.pageToken = False, None

    def parse_post_response(self, json_obj):
        result = json_obj["Result"]
        if not result:
            raise StatusError.Succeed.EmptyResult
        for each_item in result:
            item = new_comment_obj()
            item["id"] = str(each_item["Id"])
            item["referId"] = str(each_item["TravelId"])
            item["commenterId"] = str(each_item["UserId"])
            item["commenterScreenName"] = each_item["Nickname"]
            item["publishDate"] = get_timestamp(each_item["ReplyDate"])
            item["content"] = each_item["Content"]
            item["url"] = "http://m.ctrip.com/webapp/you/travels/comment/" + item["referId"]
            self.item_list.append(item)

        if int(self.adic["size"]) * (int(self.adic["pageToken"]) - 1) + len(self.item_list) < json_obj["TotalCount"]:
            self.has_next, self.pageToken = True, str(int(self.adic["pageToken"]) + 1)
        else:
            self.has_next, self.pageToken = False, None
