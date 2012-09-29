#!/usr/bin/env python
# -*- coding: utf-8 -*-
from distutils.core import setup

setup(
    name='django-mongoreversion',
    version='0.0.1-prealpha',
    description='An extension to the Django web framework that provides version control facilities for mongoengine document models. ',
    author='Steven Normore',
    author_email='snormore@gmail.com',
    long_description=open('README.md', 'r').read(),
    url='http://github.com/snormore/django-mongoreversion/',
    packages=[
        'mongoreversion',
    ],
)