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

import os
from config import TEMPLATES_DIR

import time
import datetime

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext.db import djangoforms
from google.appengine.ext import db
from google.appengine.api import memcache

from pages import CommonHandler

from ranking_engine.decorators import account_required, login_required

from ranking_engine import forms
from ranking_engine import models

import logging


class AddSiteHandler(CommonHandler):

    @login_required
    @account_required
    def get(self):
        if self.account.remaining_sites() <= 0:
            self.redirect(self.url("dashboard"))
            return
        path = os.path.join(TEMPLATES_DIR, 'site_add.html')
        template_values = self.get_common_template_values()
        template_values.update({
                'form_action' : self.url("add_site"),
                'form' : forms.SiteForm(),
                'cancel_url' : self.url("dashboard")
                });
        self.response.out.write(template.render(path, template_values))

    @login_required
    @account_required
    def post(self):
        if self.account.remaining_sites() <= 0:
            self.redirect(self.url("dashboard"))
            return
        # instance param looks ugly, but it's the only solution i found to define a parent entity with a form
        form = forms.SiteForm(data=self.request.POST,
                              instance = models.Site(parent = self.account,
                                                     account = self.account,
                                                     url = 'http://dummy.url/',
                                                     label = 'dummy'))
        if form.is_valid():
            site = form.save()
            self.redirect(self.url("add_keyword", site_key = site.key()))
            return
        else:
            path = os.path.join(TEMPLATES_DIR, 'site_add.html')
            template_values = self.get_common_template_values()
            template_values.update({
                    'form_action' : self.url("add_site"),
                    'form' : form,
                    'cancel_url' : self.url("dashboard")
                    })
            self.response.out.write(template.render(path, template_values))

class SiteHandler(CommonHandler):

    @login_required
    @account_required
    def get(self, key):
        key = db.Key(key)
        site = models.Site.get(key)
        if not site:
            self.redirect(self.url("dashboard"))
            return
        if site.account.key() !=  self.account.key():
            self.redirect(self.url("dashboard"))
            return

        ns = site.get_cache_namespace()
        output = memcache.get('site.html', ns)
        if output == None:
            path = os.path.join(TEMPLATES_DIR, 'site.html')
            template_values = self.get_common_template_values()
            template_values.update({'site' : site,
                                    'keywords' : site.keywords(),
                                    'add_keyword_url' : self.url("add_keyword", site_key=key),
                                    'remaining_keywords' : self.account.remaining_keywords()});
            output = template.render(path, template_values)
            memcache.set('site.html', output, namespace = ns)
        self.response.out.write(output)


class DeleteHandler(CommonHandler):

    @login_required
    @account_required
    def get(self, key):
        key = db.Key(key)
        site = models.Site.get(key)
        if not site:
            self.redirect(self.url("dashboard"))
            return
        if site.account.key() !=  self.account.key():
            self.redirect(self.url("dashboard"))
            return

        path = os.path.join(TEMPLATES_DIR, 'site_delete.html')
        template_values = self.get_common_template_values()
        template_values.update({'site' : site,
                                'delete_url' : self.url("delete_site", key = site.key())});
        self.response.out.write(template.render(path, template_values))


    @login_required
    @account_required
    def post(self, key):
        key = db.Key(key)
        site = models.Site.get(key)
        if not site:
            self.redirect(self.url("dashboard"))
            return
        if site.account.key() !=  self.account.key():
            self.redirect(self.url("dashboard"))
            return
        site.delete()
        self.redirect(self.url("dashboard"))

