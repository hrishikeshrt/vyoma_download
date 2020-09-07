#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vyoma Class"""

###############################################################################

import re
import os

import requests
from bs4 import BeautifulSoup
from requests_downloader.downloader import download as download_file

###############################################################################

SERVER = 'www.sanskritfromhome.in'

###############################################################################


def extract_course_id(course_url):
    try:
        not_url = '/' not in course_url
        sfh_pattern = '(http(s|)://|)(www.|)sanskritfromhome.in/course/([^/]*)'
        sfh_match = re.match(sfh_pattern, course_url)
        if not_url:
            course_id = course_url
        else:
            if sfh_match:
                course_id = sfh_match.group(len(sfh_match.groups()))
            else:
                print("Invalid course URL.")
                return None
    except Exception:
        print("Invalid course URL.")
        return None

    course_id = course_id.split('#')[0]
    return course_id

###############################################################################


class Vyoma():
    home_url = f'https://{SERVER}'
    login_url = f'https://{SERVER}/wp-admin/admin-ajax.php'

    def __init__(self, username, password, download_dir=None):
        '''
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
        '''
        self.session = requests.Session()
        self.username = username
        self.password = password
        self.logged_in = False
        self.links = {}
        self.descriptions = {}

        # download directory
        self.download_dir = download_dir
        if not download_dir:
            home_dir = os.path.expanduser('~')
            vyoma_dir = os.path.join(home_dir, 'vyoma', username)
            self.download_dir = vyoma_dir
        if not os.path.isdir(self.download_dir):
            os.makedirs(self.download_dir)

    def get_course_url(self, course_id):
        '''Build course URL from course ID'''
        return f'{self.home_url}/course/{course_id}'

    def login(self):
        '''Login to sanskritfromhome.in'''
        r = self.get(self.home_url)

        # check if already logged in
        if 'Sign Out' in r.text and 'Sign In' not in r.text:
            self.logged_in = True
            return self.logged_in

        data = {
            'user_login': self.username,
            'user_password': self.password,
            'user_action': 'login_user',
            'action': 'themex_update_user'
        }

        soup = BeautifulSoup(r.text, 'html.parser')
        nonce = soup.find('input', attrs={'name': 'nonce'})['value']
        data['nonce'] = nonce
        r = self.post(self.login_url, data=data)

        # check if it succeeded
        r = self.get(self.home_url)
        self.logged_in = ('Sign Out' in r.text and 'Sign In' not in r.text)
        return self.logged_in

    def fetch_course_page(self, course_id):
        '''Get contents of the course page

        Parameters
        ----------
        course_id : str
            Course ID.

        Raises
        ------
        RuntimeError
            If called without a valid login.

        Returns
        -------
        html
            HTML content of the course page.
        '''
        self.login()
        if not self.logged_in:
            raise RuntimeError("Requires a sign-in.")

        r = self.get(self.get_course_url(course_id))
        return r.text

    def fetch_course_links(self, course_id, html=''):
        '''
        Fetch all links of downloadable content for a course.

        Parameters
        ----------
        course_id : str
            Course ID.
        html : str, optional
            Instead of a course ID, a pre-downloaded HTML can be specified.
            The default is ''.

        Returns
        -------
        links : dict
            Links to audio, video and documents from the course.
        '''
        if not html:
            html = self.fetch_course_page(course_id)
        soup = BeautifulSoup(html, 'html.parser')
        links = {}
        links['audio'] = soup.find_all('a', attrs={'class': 'audio'})
        links['video'] = soup.find_all('a', attrs={'class': 'video'})
        links['document'] = soup.find_all('a', attrs={'class': 'document'})
        self.links[course_id] = links
        return self.links[course_id]

    def fetch_course_description(self, course_id, html=''):
        '''
        Fetch course description


        Parameters
        ----------
        course_id : str
            Course ID.
        html : str, optional
        Instead of a course ID, a pre-downloaded HTML can be specified.
        The default is ''.

        Returns
        -------
        description : str
            HTML description of the course
        '''
        if not html:
            html = self.fetch_course_page(course_id)
        soup = BeautifulSoup(html, 'html.parser')
        description_div = soup.find('div', class_='course-description')
        self.descriptions[course_id] = str(description_div)
        return self.descriptions[course_id]

    def download_course_content(self, course_id,
                                document=True, audio=True, video=True):
        '''
        Download course content (audios, documents and video-links)

        Parameters
        ----------
        course_id : str
            Course ID.
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
        html = self.fetch_course_page(course_id)
        course_dir = os.path.join(self.download_dir, course_id)
        if not os.path.isdir(course_dir):
            os.mkdir(course_dir)

        if course_id not in self.descriptions:
            self.fetch_course_description(course_id, html=html)

        with open(os.path.join(course_dir, 'description.html'), 'w') as f:
            f.write(self.descriptions[course_id])
            print("Saved course description.")

        if course_id not in self.links:
            self.fetch_course_links(course_id, html=html)

        links = self.links[course_id]

        if video:
            video_file = os.path.join(course_dir, 'video_links.txt')
            video_links = [link['href'] for link in links['video']]
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
            dl_links_file = os.path.join(course_dir, f'{dl}_links.txt')
            with open(dl_links_file, 'w') as f:
                f.write('\n'.join([link['href'] for link in links[dl]]))

            dl_dir = os.path.join(course_dir, dl)
            if not os.path.isdir(dl_dir):
                os.mkdir(dl_dir)

            downloaded = 0
            skipped = 0
            skipped_links = []
            print(f"Total {dl.title()}s:", len(links[dl]))

            for link in links[dl]:
                success = True
                try:
                    download_file(link['href'], download_dir=dl_dir,
                                  session=self.session, verbose=True)
                except Exception as e:
                    print(e)
                    success = False

                if success:
                    downloaded += 1
                else:
                    skipped += 1
                    skipped_links.append(link['href'])
                    print(f"Skipping {link['href']}")

            print(f"Successfully downloaded {downloaded} {dl} files.")
            if skipped:
                print(f"Could not download {skipped} {dl} files.")
            print(f"Skipped {dl.title()} URLs: {skipped_links}")

        if all_skipped_links:
            skipped_file = os.path.join(course_dir, 'skipped_links.txt')
            with open(skipped_file, 'w') as f:
                f.write('\n'.join(all_skipped_links))

        return True

    def download_course_audios(self, course_id):
        '''Wrapper to download only audio links'''
        return self.download_course_content(course_id, audio=True,
                                            document=False, video=False)

    def download_course_video_links(self, course_id):
        '''Wrapper to download only video links'''
        return self.download_course_content(course_id, video=True,
                                            document=False, audio=False)

    def download_course_documents(self, course_id):
        '''Wrapper to download only document links'''
        return self.download_course_content(course_id, document=True,
                                            audio=False, video=False)

    def set_user(self, username):
        self.username = username

    def set_pass(self, password):
        self.password = password

    def get(self, *args, **kwargs):
        return self.session.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        return self.session.post(*args, **kwargs)

    def __repr__(self):
        return f"Vyoma(username={self.username}, logged_in={self.logged_in})"

###############################################################################
