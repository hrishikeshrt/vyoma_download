#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vyoma Session

@author: Hrishikesh Terdalkar
"""

from collections import defaultdict
import json
import os
from typing import Dict

from tqdm import tqdm

from .edmingle import EdmingleAPI
from .utils import pretty_name
from .verbose_logger import install as install_logger

###############################################################################

install_logger()

###############################################################################

VYOMA_HOSTNAME = "learn.sanskritfromhome.org"
VYOMA_API_HOST = "vyoma-api.edmingle.com"

###############################################################################


class Vyoma(EdmingleAPI):
    def __init__(self, username: str, password: str, download_dir: str = None):
        """
        Vyoma Session

        Parameters
        ----------
        username : str
            Username.
        password : str
            Password.
        download_dir : str, optional
            Location in which the course content will be downloaded.
            The default is None.
        """

        super().__init__(
            username=username,
            password=password,
            hostname=VYOMA_HOSTNAME,
            api_host=VYOMA_API_HOST,
        )
        self.login()

        # download directory
        self.download_dir = download_dir

        if not download_dir:
            home_dir = os.path.expanduser("~")
            vyoma_dir = os.path.join(home_dir, "vyoma", self.user["username"])
            self.download_dir = vyoma_dir
        if not os.path.isdir(self.download_dir):
            os.makedirs(self.download_dir)

    def find_course(self, search_pattern: str) -> str:
        response = self.get_courses(search_pattern=search_pattern)
        courses = []
        for batch in response.get("batches", []):
            if batch.get("master_batch_id"):
                courses.append({
                    "course_id": batch.get("master_batch_id"),
                    "course_name": batch.get("master_batch_name"),
                    "course_instructor": batch.get("tutor_name")
                })
        return courses

    def download_section(self, class_id: str, section_id: str) -> Dict:
        raise NotImplementedError

    def download_course(self, course_id: str, fetch_audio: bool = False, fetch_document: bool = True) -> Dict:
        """Download Course Content

        Parameters
        ----------
        course_id : str
            Course ID from Vyoma Edmingle Platform
        fetch_audio : bool, optional
            If true, the audios are downloaded.
            The default is True.
        fetch_document : bool, optional
            If true, the adocuments are downloaded.
            The default is True.

        Returns
        -------
        Dict
            Complete download log
        """
        c_response = self.get_course_classes(course_id)
        course = c_response["courses"][0]
        class_id = course["class_id"]
        class_name = course["class_name"]
        class_name_pretty = pretty_name(class_name)
        tutor_name = course["tutor_name"]
        print(f"Course: {class_name}")
        print(f"Teacher: {tutor_name}")
        course_dir = os.path.join(self.download_dir, class_name_pretty)
        if not os.path.isdir(course_dir):
            os.makedirs(course_dir)

        cr_response = self.get_class_resources(class_id)
        course_sections = cr_response["sections"]

        # logs
        course_log = {
            "course_id": course_id,
            "class_id": class_id,
            "class_name": class_name,
            "class_name_pretty": class_name_pretty,
            "tutor_name": tutor_name,
            "num_exercises": course["stats"]["course_num_exercises"],
            "num_materials": course["stats"]["course_num_materials"],
            "local_path": course_dir
        }
        section_log = []
        material_log = {
            "file": defaultdict(list),
            "external_url": defaultdict(list),
            "html_text": [],
            "failed": [],
            "unknown": []
        }
        print(f"Found {len(course_sections)} sections.")

        for section_details in course_sections:
            section_id = section_details[0]
            sr_response = self.get_section_resources(class_id, section_id)

            section = sr_response["section"]
            section_name = section["name"]
            section_resources = sr_response["resources"]
            section_log.append({
                "id": section_id,
                "name": section_name,
                "num_materials": section["num_materials"]
            })
            print(f"Downloading from '{section_name}' ...")

            for section_resource in tqdm(section_resources):
                material_id = section_resource[1]
                material_name = section_resource[3]
                material_type = section_resource[4]
                material_source = section_resource[-3]

                m_response = self.get_material(class_id, material_id)
                success_message = "Teaching material retrieved successfully"
                if m_response["message"] != success_message:
                    material_log["failed"].append({
                        "section_id": section_id,
                        "id": material_id,
                        "name": material_name,
                        "type": material_type,
                        "source": material_source,
                        "response": m_response
                    })
                    continue

                material = m_response["material"]
                if material_source == "file":
                    material_url = material["url"]
                    material_filename = material["file_name"]
                    material_path = os.path.join(course_dir, material_filename)
                    self.download_material(material_url, material_path)
                    material_log[material_source][material_type].append({
                        "section_id": section_id,
                        "id": material_id,
                        "name": material_name,
                        "type": material_type,
                        "filename": material_filename,
                        "local_path": material_path
                    })
                elif material_source == "external_url":
                    material_url = material["external_url"]
                    material_log[material_source][material_type].append({
                        "section_id": section_id,
                        "id": material_id,
                        "name": material_name,
                        "type": material_type,
                        "external_url": material_url
                    })
                elif material_source == "html_text":
                    material_log[material_source].append({
                        "section_id": section_id,
                        "id": material_id,
                        "name": material_name,
                        "type": material_type,
                        "html": material["html_text"]
                    })
                else:
                    material_log["unknown"].append({
                        "section_id": section_id,
                        "id": material_id,
                        "name": material_name,
                        "type": material_type,
                        "source": material_source,
                        "material": material
                    })

        download_log = {
            "course": course_log,
            "section": section_log,
            "material": material_log
        }
        with open(os.path.join(course_dir, "log.json"), "w") as f:
            json.dump(download_log, f, indent=2, ensure_ascii=False)

        material_count = {}
        for k, v in material_log.items():
            if isinstance(v, dict):
                material_count[k] = {}
                for k1, v1 in v.items():
                    material_count[k][k1] = len(v1)
            if isinstance(v, list):
                material_count[k] = len(v)

        print("material:", json.dumps(material_count, indent=2))
        return download_log

    def show_course_status(self, course_id: str):
        c_response = self.get_course_classes(course_id)
        course = c_response["courses"][0]
        class_id = course["class_id"]
        class_name = course["class_name"]
        class_name_pretty = pretty_name(class_name)
        tutor_name = course["tutor_name"]
        print(f"Course: {class_name}")
        print(f"Teacher: {tutor_name}")

        course_dir = os.path.join(self.download_dir, class_name_pretty)
        if not os.path.isdir(course_dir):
            print("Course has not been downloaded yet.")
            return

        if not os.path.isfile(os.path.join(course_dir, "log.json")):
            print("No saved download log found.")
            return

        print(f"Local Path: {course_dir}")
        with open(os.path.join(course_dir, "log.json"), encoding="utf-8") as f:
            download_log = json.load(f)

        material_count = {}
        for k, v in download_log["material"].items():
            if isinstance(v, dict):
                material_count[k] = {}
                for k1, v1 in v.items():
                    material_count[k][k1] = len(v1)
            if isinstance(v, list):
                material_count[k] = len(v)

        print("material:", json.dumps(material_count, indent=2))

###############################################################################
