#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `frkl_project_meta` package."""

import frkl.project_meta
import pytest  # noqa


def test_assert():

    assert frkl.project_meta.get_version() is not None
