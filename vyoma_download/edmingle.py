#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Edmingle API

@author: Hrishikesh Terdalkar
"""

import json
import logging
from functools import cached_property
from typing import Dict

import requests
from requests_downloader import download

###############################################################################

PROTOCOL = "https:"
ENDPOINT = "/nuSource/api/v1"

###############################################################################


class EdmingleAPI:
    def __init__(
        self,
        username: str,
        password: str,
        hostname: str,
        api_host: str,
        endpoint: str = ENDPOINT,
        protocol: str = PROTOCOL,
    ):
        """Edmingle API"""

        self.protocol = protocol
        self.hostname = hostname
        self.api_endhost = api_host
        self.api_endpoint = f"{protocol}//{api_host}{endpoint}"
        self.host = f"{protocol}//{hostname}"

        self.username = username
        self.password = password
        self.apikey = None
        self.logged_in = False

        self.user = {}
        self.usermeta = {}
        self.user_classes = {}
        self.organization = {}

        self.session = requests.Session()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)

    # ----------------------------------------------------------------------- #

    def login(self) -> bool:
        """Login to Edmingle Platform

        Returns
        -------
        bool
            Indicates whether the login was successful
        """

        path = "tutor/login"
        data = {
            "username": self.username,
            "password": self.password,
            "persistent_login": True,
        }
        data = {"JSONString": json.dumps(data)}
        response = self.api(path=path, data=data, method="post")
        if response["message"] == "Login successful":
            self.logger.info("Login successful")
            self.logged_in = True
            self.user = response["user"]
            self.apikey = response["user"]["apikey"]
        else:
            self.logger.error("Login failed")

        if self.logged_in:
            response = self.get_usermeta()
            if response["message"] == "Success":
                self.usermeta = response["user"]
                if response["user"]["org_data"]:
                    self.organization = response["user"]["org_data"][0]
                if response["user_classes"]:
                    self.user_classes = {
                        str(k): {} for k in response["user_classes"]
                    }

        return self.logged_in

    # ----------------------------------------------------------------------- #

    def get_meta_all(self) -> Dict:
        path = "meta/all"
        data = {"institution_id": self.organization.get("institution_id", "")}
        return self.api(path=path, data=data)

    # ----------------------------------------------------------------------- #

    def get_user_basicinfo(self) -> Dict:
        path = "user/basicinfo"
        return self.api(path=path)

    def get_usermeta(self) -> Dict:
        path = "user/usermeta"
        return self.api(path=path)

    # ----------------------------------------------------------------------- #

    def get_courses(
        self, search_pattern: str = "", tag_ids: str = "9"
    ) -> Dict:
        path = "student/masterbatches"
        data = {"tag_ids": tag_ids, "search": search_pattern}
        return self.api(path=path, data=data)

    # ----------------------------------------------------------------------- #

    def get_classes_period(self, date) -> Dict:
        path = "student/classes/period"
        data = {"date": date}
        return self.api(path=path, data=data)

    # ----------------------------------------------------------------------- #

    def get_course_classes(self, course_id: str) -> Dict:
        path = f"student/masterbatches/classes/{course_id}"
        data = {"get_tags": 1, "show_overview": 1}
        return self.api(path=path, data=data)

    def get_class_resources(self, class_id: str) -> Dict:
        path = f"student/classcurriculum/{class_id}/resources"
        return self.api(path=path)

    def get_section_resources(self, class_id: str, section_id: str) -> Dict:
        path = f"student/sections/{section_id}/resources"
        data = {"class_id": class_id}
        return self.api(path=path, data=data)

    def get_material(self, class_id: str, material_id: str) -> Dict:
        path = f"student/materials/{material_id}"
        data = {"class_id": class_id}
        return self.api(path=path, data=data)

    # ----------------------------------------------------------------------- #

    def get_certificates(self) -> Dict:
        path = "certificates/students"
        return self.api(path=path)

    # ----------------------------------------------------------------------- #

    def api(
        self,
        path: str,
        data: Dict = None,
        is_json: bool = True,
        method: str = "GET",
    ) -> Dict or str:
        """General API Query

        Parameters
        ----------
        path : str
            API Path
        data : Dict, optional
            Dictionary containing GET or POST data
            In case of "GET", the data is used to form the GET options string.
            In case of "POST", the data is passed with the POST request.
            The default is None
        is_json : bool, optional
            Is the response a JSON object?
            The default is True
        method : str, optional
            HTTP Method ("GET" or "POST").
            The default is "GET"

        Returns
        -------
        Dict or str
            Dict, if is_json is True
            str, otherwise
        """

        methods = ["GET", "POST"]
        default_method = "GET"

        method = method.upper()
        if method not in methods:
            method = default_method

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "APIKEY": self.apikey,
            "Connection": "keep-alive",
            "ORGID": str(self.organization.get("organization_id", "")),
            "Origin": self.host,
            "DNT": "1",
            "Connection": "keep-alive",
            "Referer": self.host,
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "Sec-GPC": "1",
            "TE": "trailers",
        }
        data = data or {}
        if method == "GET":
            option_string = "&".join(f"{k}={v}" for k, v in data.items())
            api_url = f"{self.api_endpoint}/{path}?{option_string}"
            r = self.session.get(api_url, headers=headers)
        if method == "POST":
            api_url = f"{self.api_endpoint}/{path}"
            r = self.session.post(api_url, data=data, headers=headers)

        content = r.content.decode()
        if is_json:
            return json.loads(content.strip())
        else:
            return content

    # ----------------------------------------------------------------------- #

    def download_material(self, url: str, path: str) -> str or None:
        headers = {
            "User-Agent": self.user_agent,
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Referer": self.host,
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "iframe",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Sec-GPC": "1",
        }
        return download(
            url, download_path=path, headers=headers, session=self.session
        )

    # ----------------------------------------------------------------------- #

    @cached_property
    def user_agent(self) -> str:
        return (
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:92.0) "
            "Gecko/20100101 Firefox/92.0"
        )


###############################################################################
