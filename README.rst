==============
vyoma-download
==============


.. image:: https://img.shields.io/pypi/v/vyoma_download.svg
        :target: https://pypi.python.org/pypi/vyoma_download

.. image:: https://img.shields.io/travis/hrishikeshrt/vyoma_download.svg
        :target: https://travis-ci.com/hrishikeshrt/vyoma_download

.. image:: https://readthedocs.org/projects/vyoma-download/badge/?version=latest
        :target: https://vyoma-download.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status




Download course contents from sanskritfromhome.in

* Free software: MIT license
* Documentation: https://vyoma-download.readthedocs.io.

Usage
-----

To use vyoma-download in a project::

    from vyoma_download.vyoma_download import Vyoma
    vyoma = Vyoma(username, password)
    login_successful = vyoma.login()

To use vyoma-download from command line::

    vyoma-download [course_id|course_url]

**Note**:

You must be registered on https://sanskritfromhome.in/.

You must be subscribed to the course that you wish to download.


Features
--------

* Download video, audio and documents for courses from sanskritfromhome.in
* Resume download whenever possible
* Keep a list of files that fail to download

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
