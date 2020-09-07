=====
Usage
=====

To use vyoma-download in a project::

    from vyoma_download.vyoma_download import Vyoma
    vyoma = Vyoma(username, password)
    login_successful = vyoma.login()


To use vyoma-download binary::

    vyoma-download [course_id|course_url]