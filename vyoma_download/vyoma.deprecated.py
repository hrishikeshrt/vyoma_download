#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vyoma Class"""

###############################################################################

import re
import os
import json
import logging
from datetime import datetime as dt
from dataclasses import dataclass, asdict

import requests
from bs4 import BeautifulSoup
from requests_downloader.downloader import download as download_file

###############################################################################

import vyoma_download.verbose_logger as verbose_logger
verbose_logger.install()

###############################################################################

SERVER = 'sanskritfromhome.in'

###############################################################################


@dataclass
class Link:
    url: str
    type: str
    path: str = None
    date: str = None
    complete: bool = False

###############################################################################


class Course:
    base_url = f'https://www.{SERVER}/course'
    pattern = f'(http(s|)://|)(www.|){SERVER}/course/([^/]*)'

    def __init__(self, url_or_id, user):
        '''
        Course Class

        Parameters
        ----------
        url_or_id: str
            Course URL (or simply the ID part of the course URL)
        user: User or tuple
            Instance of User class
            Alternatively, a tuple of one of the following forms
            - (username, password)
            - (username, password, download_dir)
        '''
        self.logger = logging.getLogger(__name__)
        self.id = self.extract_id(url_or_id)
        self.url = f'{self.base_url}/{self.id}' if self.id else None
        self.html = None
        self.links = {}
        self.subscribed = None

        self.user = None
        if isinstance(user, User):
            self.user = user
        elif isinstance(user, tuple) and len(user) in [2, 3]:
            self.user = User(*user)
        else:
            self.logger.error(
                "Invalid user specified. "
                "Must be an instance of `User` or a `tuple`."
            )

        if self.user is not None:
            self.location = os.path.join(self.user.download_dir, self.id)
            self._progress_file = os.path.join(self.location, '.progress.json')
            os.makedirs(self.location, exist_ok=True)
            self.logger.verbose(f"Course Directory: '{self.location}'")
            self.extract_information(latest=True)

        self.logger.debug(f"{self.user}")
        self.logger.debug(f"{self}")

    def extract_id(self, url_or_id):
        '''Extract course ID from a URL'''
        try:
            not_url = '/' not in url_or_id
            _match = re.match(self.pattern, url_or_id)
            if not_url:
                course_id = url_or_id
            else:
                if _match:
                    course_id = _match.group(len(_match.groups()))
                else:
                    self.logger.warning("Invalid course URL.")
                    return None
        except Exception:
            self.logger.warning("Invalid course URL.")
            return None

        course_id = course_id.split('#')[0]
        return course_id

    def fetch_page(self):
        '''
        Get contents of the course page

        Raises
        ------
        RuntimeError
            If called without a valid login.

        Returns
        -------
        html
            HTML content of the course page.
        '''
        r = self.get(self.url)
        self.html = r.text
        self.soup = BeautifulSoup(self.html, 'lxml')
        self.logger.verbose("Downloaded course page.")
        return self.html

    def extract_information(self, latest=False):
        '''Extract meta information from a course page'''
        if not self.html or latest:
            self.fetch_page()

        # Course Information
        description_div = self.soup.find('div', class_='course-description')
        self.description = str(description_div)

        header_div = self.soup.find('header', class_='course-header')
        # self.header = str(header_div)
        # footer_div = description_div.find('footer', class_='course-footer')
        # self.footer = str(footer_div)

        if header_div:
            course_url_element = header_div.find('a')
            if course_url_element and course_url_element.has_attr('href'):
                if self.extract_id(course_url_element['href']) != self.id:
                    self.logger.error("Invalid course header.")

            if header_div.find('h5') and header_div.find('h5').find('b'):
                self.title = header_div.find('h5').find('b').get_text().strip()
            else:
                self.title = self.id

            teacher_element = header_div.find('a', class_='author')
            if teacher_element:
                self.teacher = teacher_element.get_text().strip()
            else:
                self.teacher = ''

        # Subscription Information
        id_input = self.soup.find('input', attrs={'name': 'course_id'})
        course_form = id_input.find_parent('form')
        form_inputs = course_form.find_all('input')
        self._subscription_data = {
            el['name']: el['value']
            for el in form_inputs
        }
        if self._subscription_data.get('course_action') == 'add_user':
            self.subscribed = False
        elif self._subscription_data.get('course_action') == 'remove_user':
            self.subscribed = True
        else:
            self.logger.error("Course subscription button not found.")

        self.logger.debug(f"Subscribed: {self.subscribed}")

    def subscribe(self):
        '''Subscribe to the course'''
        self.extract_information(latest=True)
        if not self.subscribed:
            self.logger.info("Subscribing to the course ...")
            self.post(self.url, data=self._subscription_data)
            self.extract_information(latest=True)
            if not self.subscribed:
                self.logger.error("Could not subscribe to the course.")
            else:
                self.logger.info("Subscription successful.")
        else:
            self.logger.info("Already subscribed to the course.")

        return self.subscribed

    def fetch_links(self):
        '''
        Fetch all links of downloadable content for a course.

        Returns
        -------
        links : dict
            Links to audio, video and documents from the course.
        '''
        if not self.subscribed:
            self.subscribe()
            if not self.subscribed:
                self.logger.error("Could not fetch content links.")
                return False

        soup = self.soup
        links = self.links
        link_classes = ['document', 'audio', 'video']
        for link_class in link_classes:
            links[link_class] = [
                link['href'] for link in soup.find_all('a', class_=link_class)
                if link.has_attr('href')
            ]
            self.logger.verbose(
                f"Identified {len(links[link_class])} {link_class} links."
            )

        return links

    def download_content(self, document=True, audio=True, video=True):
        '''
        Download course content (audios, documents and video-links)

        Parameters
        ----------
        document : bool, optional
            If True, download document links.
            The default is True.
        audio : bool, optional
            If True, download audio links.
            The default is True.
        video : bool, optional
            If True, download video links.
            The default is True.

        Returns
        -------
        status : bool
            True if the download funcion completed successfully.
            Does not mean that all the files were downloaded successfully.
        '''
        if not self.subscribed:
            self.subscribe()
            if not self.subscribed:
                self.logger.error("Could not download the content.")
                return False

        with open(os.path.join(self.location, 'description.html'), 'w') as f:
            f.write(self.description)
            self.logger.verbose("Saved course description.")

        links = self.fetch_links() if not self.links else self.links

        # Load last progress
        self.load_progress()
        for _type, _links in links.items():
            for _link in _links:
                if _link not in self.progress:
                    self.progress[_link] = Link(url=_link, type=_type)

        if video:
            video_file = os.path.join(self.location, 'video_links.txt')
            video_links = [link for link in links['video']]
            with open(video_file, 'w') as f:
                f.write('\n'.join(video_links))

        download = []
        if document:
            download.append('document')

        if audio:
            download.append('audio')

        all_skipped_links = []
        for dl in download:
            # save links
            dl_links_file = os.path.join(self.location, f'{dl}_links.txt')
            with open(dl_links_file, 'w') as f:
                f.write('\n'.join([link for link in links[dl]]))

            dl_dir = os.path.join(self.location, dl)
            os.makedirs(dl_dir, exist_ok=True)

            count = 0
            skip = 0
            skipped_links = []
            self.logger.info(f"Total {dl.title()}s: {len(links[dl])}")

            for _link in links[dl]:
                link = self.progress[_link]
                if link.complete:
                    self.logger.debug(f"{link}")
                    if os.path.isfile(link.path):
                        _path_basename = os.path.basename(link.path)
                        self.logger.info(
                            f"File '{_path_basename}' is already downloaded!"
                        )
                        continue
                    else:
                        self.logger.info(
                            f"File '{_path_basename}' is missing."
                        )
                        link.path = None
                        link.date = None
                        link.complete = False

                try:
                    download_path = download_file(
                        link.url,
                        download_dir=dl_dir,
                        session=self.user.session
                    )
                    success = bool(download_path)
                except Exception:
                    self.logger.exception(
                        f"An error occurred while downloading '{link.url}'."
                    )
                    success = False

                if success:
                    count += 1
                    link.path = download_path
                    link.date = dt.strftime(dt.now(), '%Y.%m.%d')
                    link.complete = True
                    self.save_progress()
                else:
                    skip += 1
                    skipped_links.append(link.url)
                    self.logger.warning(f"Skipping {link.url}")

                self.logger.debug(f"{link}")

            self.logger.info(f"Successfully downloaded {count} {dl} files.")
            if skip:
                self.logger.warning(f"Could not download {skip} {dl} files.")
            self.logger.info(f"Skipped {dl.title()} URLs: {skipped_links}")

        if all_skipped_links:
            skipped_file = os.path.join(self.location, 'skipped_links.txt')
            with open(skipped_file, 'w') as f:
                f.write('\n'.join(all_skipped_links))

        return True

    def download_audios(self):
        '''Wrapper to download only audio links'''
        return self.download_content(audio=True, document=False, video=False)

    def download_video_links(self, course_id):
        '''Wrapper to download only video links'''
        return self.download_content(video=True, document=False, audio=False)

    def download_documents(self, course_id):
        '''Wrapper to download only document links'''
        return self.download_content(document=True, audio=False, video=False)

    # ----------------------------------------------------------------------- #

    def show_status(self):
        '''Show the status of the course content'''
        links = self.fetch_links() if not self.links else self.links

        # Load last progress
        self.load_progress()
        for _type, _links in links.items():
            for _link in _links:
                if _link not in self.progress:
                    self.progress[_link] = Link(url=_link, type=_type)

        information = {
            'id': self.id,
            'title': self.title,
            'teacher': self.teacher
        }
        status = {}
        for _, link in self.progress.items():
            if link.type not in status:
                status[link.type] = {'total': 0, 'downloaded': 0}
            status[link.type]['total'] += 1
            status[link.type]['downloaded'] += link.complete

        for k, v in status.items():
            v['percent'] = (
                round((v['downloaded'] / v['total']) * 100, 2)
                if v['total'] else
                0
            )

        information.update(status)
        print(json.dumps(information, ensure_ascii=False, indent=2))
        return information

    def load_progress(self):
        '''
        Load download progress

        Progress is a dictionary of links with meta-information.
        Meta-information is a dictionary, loaded as an instance of Link().
        '''
        if os.path.isfile(self._progress_file):
            try:
                with open(self._progress_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.progress = {
                        k: Link(**v) for k, v in data.items()
                    }
                    self.logger.verbose("Loaded progress information.")
            except Exception:
                self.logger.warning("Invalid progress information.")
                self.progress = {}
        else:
            self.progress = {}

    def save_progress(self):
        '''
        Save download progress

        Link() class is serialized asdict() for each link.
        Links are then stored as a dictionary.
        '''
        with open(self._progress_file, 'w', encoding='utf-8') as f:
            json.dump({
                k: asdict(v)
                for k, v in self.progress.items()
            }, f, indent=2, ensure_ascii=False)
            self.logger.verbose("Saved progress information.")

    # ----------------------------------------------------------------------- #

    def get(self, *args, **kwargs):
        return self.user.session.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        return self.user.session.post(*args, **kwargs)

    # ----------------------------------------------------------------------- #

    def __repr__(self):
        return f"Course(id={self.id}, subscribed={self.subscribed})"

###############################################################################


class User:
    home_url = f'https://www.{SERVER}'
    login_url = f'https://www.{SERVER}/wp-admin/admin-ajax.php'

    def __init__(self, username, password, download_dir=None):
        '''
        Vyoma User Session

        Parameters
        ----------
        username : str
            Username.
        password : str
            Password.
        download_dir : str, optional
            Location in which the course content will be downloaded.
            The default is None.
        '''
        self.session = requests.Session()
        self.username = username
        self.password = password
        self.logged_in = False
        self.logger = logging.getLogger(__name__)

        # download directory
        self.download_dir = download_dir
        if not download_dir:
            home_dir = os.path.expanduser('~')
            vyoma_dir = os.path.join(home_dir, 'vyoma', username)
            self.download_dir = vyoma_dir

        os.makedirs(self.download_dir, exist_ok=True)
        self.logger.verbose(f"Download Directory: '{self.download_dir}'")

    def login(self):
        '''Login to sanskritfromhome.in'''
        r = self.get(self.home_url)

        # check if already logged in
        if 'Sign Out' in r.text and 'Sign In' not in r.text:
            self.logged_in = True
            self.logger.verbose("Already logged in!")
            return self.logged_in

        data = {
            'user_login': self.username,
            'user_password': self.password,
            'user_action': 'login_user',
            'action': 'themex_update_user'
        }

        soup = BeautifulSoup(r.text, 'lxml')
        nonce = soup.find('input', attrs={'name': 'nonce'})['value']
        data['nonce'] = nonce
        r = self.post(self.login_url, data=data)

        # check if it succeeded
        r = self.get(self.home_url)
        self.logged_in = ('Sign Out' in r.text and 'Sign In' not in r.text)
        self.logger.verbose(
            f"Login as '{self.username}' "
            f"{'successful' if self.logged_in else 'failed'}."
        )
        return self.logged_in

    def get_courses(self):
        self.logger.warning("Feature not implemented yet.")

    def get(self, *args, **kwargs):
        return self.session.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        return self.session.post(*args, **kwargs)

    def __repr__(self):
        return f"User(username={self.username}, logged_in={self.logged_in})"

###############################################################################
