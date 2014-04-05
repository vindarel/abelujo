#!/bin/env python
# -*- coding: utf-8 -*-
import unittest

def suite():
    return unittest.TestLoader().discover("search.tests", pattern="*.py")
