=====
Usage
=====

To use vyoma-download in a project::

    from vyoma_download.vyoma_download import User, Course
    vyoma = User(username, password)
    login_successful = vyoma.login()
    course = Course(course_url, user=vyoma)
    course.fetch_links()
    course.download_content()


To use vyoma-download binary::

    vyoma-download [course_id|course_url]