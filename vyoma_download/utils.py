#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utility Scripts
@author: Hrishikesh Terdalkar
"""

###############################################################################


def pretty_name(coursename: str) -> str:
    table = str.maketrans({
        "-": " ", ":": " ", "&": " and ", "(": " ", ")": " "
    })
    return "_".join(coursename.lower().translate(table).split())


###############################################################################
