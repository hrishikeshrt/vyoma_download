#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Console script for vyoma_download."""

###############################################################################

import os
import sys
import stat
import getpass
import logging
import argparse

from . import __version__
from vyoma_download.vyoma_download import User, Course
import vyoma_download.verbose_logger as verbose_logger

###############################################################################

verbose_logger.install()

# --------------------------------------------------------------------------- #

root_logger = logging.getLogger()
root_logger.addHandler(logging.StreamHandler()),
root_logger.setLevel(logging.INFO)

# --------------------------------------------------------------------------- #

logger = logging.getLogger(__name__)

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
                   help="Path of the directory to download content to")
    p.add_argument("-u", "--username", default=None)
    p.add_argument("-p", "--password", default=None)
    p.add_argument('--verbose',
                   help='Enable verbose output',
                   action='store_true')
    p.add_argument('--debug',
                   help='Enable debug information',
                   action='store_true')
    p.add_argument('--version',
                   action='version',
                   version='%(prog)s ' + __version__)

    args = vars(p.parse_args())

    if args['verbose']:
        root_logger.setLevel(verbose_logger.VERBOSE)
    if args['debug']:
        root_logger.setLevel(logging.DEBUG)

    # credentials
    config = {}

    home_dir = os.path.expanduser('~')
    config_file = os.path.join(home_dir, '.vyoma.cfg')
    if os.path.isfile(config_file):
        with open(config_file) as f:
            lines = f.read().split('\n')
            for line in lines:
                if line.strip():
                    key, value = line.split('=')
                config[key.strip()] = value.strip()

    username = (
        args['username'] or
        os.environ.get('VYOMA_USER') or
        config.get('username')
    )
    password = (
        args['password'] or
        os.environ.get('VYOMA_PASS') or
        config.get('password')
    )
    manual = not (username and password)

    if not username:
        username = input('Username: ')
    if not password:
        password = getpass.getpass('Password: ')
    username = username.strip()
    password = password.strip()

    # action
    vyoma_user = User(
        username=username,
        password=password,
        download_dir=args['output']
    )
    if not vyoma_user.login():
        logging.error("Could not sign-in. Are the credentials correct?")
        return 1

    if manual:
        answer = input("Save credentials for future use? (Y/n)")
        if not answer or answer.lower()[0] == 'y':
            with open(config_file, 'w') as f:
                f.write(f"username = {username}\n"
                        f"password = {password}")
            logging.info("Credentials saved!")
            os.chmod(config_file, stat.S_IREAD + stat.S_IWRITE)

    if vyoma_user.logged_in:
        course = Course(args['course-url'], user=vyoma_user)
        course.fetch_links()
        if not(any([args['audio'], args['video'], args['document']])):
            course.download_content()
        else:
            course.download_content(
                document=args['document'],
                audio=args['audio'],
                video=args['video']
            )
    return 0

###############################################################################


if __name__ == "__main__":
    sys.exit(main())

###############################################################################
