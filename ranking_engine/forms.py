#
# Copyright 2010 Matthieu Huguet
#
# This file is part of SEO Ranking Engine.
#
# SEO Ranking Engine is free  software: you can redistribute it and/or
# modify it under  the terms of the GNU  Lesser General Public License
# as published  by the Free  Software Foundation, either version  3 of
# the License, or (at your option) any later version.
#
# SEO  Ranking Engine  is  distributed in  the  hope that  it will  be
# useful, but WITHOUT ANY  WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with SEO Ranking Engine.  If not, see
# <http://www.gnu.org/licenses/>.

from google.appengine.ext import db
from google.appengine.ext.db import djangoforms

from django import forms

from django.forms.widgets import CheckboxSelectMultiple
from django.forms.util import ValidationError


import datetime
from models import Site, Keyword
from config import search_engines, available_search_engines



import logging

class SiteForm(djangoforms.ModelForm):
    class Meta:
        model = Site
        exclude = ['account', 'created_at']


class KeywordForm(djangoforms.ModelForm):
    class Meta:
        model = Keyword
        exclude = ['site', 'created_at', 'last_update']

    choices = []
    for i in available_search_engines:
        choices.append((i, search_engines[i].get('label')))
    server = forms.fields.MultipleChoiceField(choices = choices, label = "Search Engines", widget = CheckboxSelectMultiple)
