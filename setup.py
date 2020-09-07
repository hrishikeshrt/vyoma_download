#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ["requests", "requests-downloader", "beautifulsoup4"]

setup_requirements = []

test_requirements = []

setup(
    author="Hrishikesh Terdalkar",
    author_email='hrishikeshrt@linuxmail.org',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Download course contents from sanskritfromhome.in",
    entry_points={
        'console_scripts': [
            'vyoma-download=vyoma_download.cli:main',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='vyoma_download',
    name='vyoma_download',
    packages=find_packages(include=['vyoma_download', 'vyoma_download.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/hrishikeshrt/vyoma_download',
    version='0.1.0',
    zip_safe=False,
)
