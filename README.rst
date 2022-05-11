==============
vyoma-download
==============

.. image:: https://img.shields.io/pypi/v/vyoma_download?color=success
        :target: https://pypi.python.org/pypi/vyoma_download

.. image:: https://readthedocs.org/projects/vyoma-download/badge/?version=latest
        :target: https://vyoma-download.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status

.. image:: https://img.shields.io/pypi/pyversions/vyoma_download
        :target: https://pypi.python.org/pypi/vyoma_download
        :alt: Python Version Support

.. image:: https://img.shields.io/github/issues/hrishikeshrt/vyoma_download
        :target: https://github.com/hrishikeshrt/vyoma_download/issues
        :alt: GitHub Issues

.. image:: https://img.shields.io/github/followers/hrishikeshrt?style=social
        :target: https://github.com/hrishikeshrt
        :alt: GitHub Followers

.. image:: https://img.shields.io/twitter/follow/hrishikeshrt?style=social
        :target: https://twitter.com/hrishikeshrt
        :alt: Twitter Followers


Download course contents from sanskritfromhome.org

* Free software: MIT license
* Documentation: https://vyoma-download.readthedocs.io.

Features
========

* Download video, audio and documents for courses from sanskritfromhome.org
* Resume download whenever possible
* Keep a list of files that fail to download

Usage
=====

Use in a Project
----------------

To use vyoma-download in a project:

.. code-block:: python

    from vyoma_download.vyoma import Vyoma
    vyoma = Vyoma(username, password)
    courses = vyoma.find_course("LSK")
    course_id = courses[0]["course_id"]
    vyoma.download_course(course_id)


Use Console Interface
---------------------

.. code-block:: console

    usage: vyoma-dl [-h] [-a] [-d] [-o OUTPUT]
                    [-u USERNAME] [-p PASSWORD]
                    [--status] [--verbose]
                    [--debug] [--version] course-pattern

    Download course contents from 'sanskritfromhome.in'.

    positional arguments:
    course-pattern        URL of the relevant course

    optional arguments:
      -h, --help            show this help message and exit
      -a, --audio           Download audios only
      -d, --document        Download documents only
      -o OUTPUT, --output OUTPUT
                            Path to the download directory
      -u USERNAME, --username USERNAME
      -p PASSWORD, --password PASSWORD
      --status              Display status of the current course
      --verbose             Enable verbose output
      --debug               Enable debug information
      --version             show program's version number and exit

**Note**:

You must be registered on https://sanskritfromhome.org/.

You must be subscribed to the course that you wish to download.
