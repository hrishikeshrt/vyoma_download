#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Console script for vyoma_download."""

###############################################################################

import os
import sys
import stat
import getpass
import argparse

from vyoma_download.vyoma_download import Vyoma, extract_course_id

###############################################################################


def main():
    desc = "Download course contents from 'sanskritfromhome.in'."

    p = argparse.ArgumentParser(description=desc)
    p.add_argument("course-url", help="URL of the relevant course")
    p.add_argument("-v", "--video", action='store_true',
                   help="Download video links only")
    p.add_argument("-a", "--audio", action='store_true',
                   help="Download audios only")
    p.add_argument("-d", "--document", action='store_true',
                   help="Download documents only")
    p.add_argument("-o", "--output", default=None,
                   help="Path of the directory to download content to.")
    p.add_argument("-u", "--username", default=None)
    p.add_argument("-p", "--password", default=None)
    args = vars(p.parse_args())

    # download options
    course_url = args['course-url']
    audio = args['audio']
    video = args['video']
    document = args['document']
    output = args['output']

    # credentials
    config = {}

    home_dir = os.path.expanduser('~')
    config_file = os.path.join(home_dir, '.vyoma.cnf')
    if os.path.isfile(config_file):
        with open(config_file) as f:
            lines = f.read().split('\n')
            for line in lines:
                if line.strip():
                    key, value = line.split('=')
                config[key.strip()] = value.strip()

    username = (
        config.get('username') or
        os.environ.get('VYOMA_USER') or
        args['username']
    )
    password = (
        config.get('password') or
        os.environ.get('VYOMA_PASS') or
        args['password']
    )
    manual = not (username and password)

    if not username:
        username = input('Username: ')
    if not password:
        password = getpass.getpass('Password: ')
    username = username.strip()
    password = password.strip()

    # action
    vyoma = Vyoma(username=username, password=password, download_dir=output)
    if not vyoma.login():
        print("Error: could not sign in.")
        return 1

    if manual:
        answer = input("Save credentials for future use? (Y/n)")
        if not answer or answer.lower()[0] == 'y':
            with open(config_file, 'w') as f:
                f.write(f"username = {username}\n"
                        f"password = {password}")
            print("Credentials saved!")
            os.chmod(config_file, stat.S_IREAD + stat.S_IWRITE)

    if vyoma.logged_in:
        course_id = extract_course_id(course_url)
        vyoma.fetch_course_links(course_id)
        if not(any([audio, video, document])):
            vyoma.download_course_content(course_id)
        else:
            vyoma.download_course_content(course_id,
                                          document=document,
                                          audio=audio,
                                          video=video)
    return 0

###############################################################################


if __name__ == "__main__":
    sys.exit(main())

###############################################################################
