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

from google.appengine.ext.webapp import template
from google.appengine.ext import db

from pages import CommonHandler
from routes import url_for

from ranking_engine.decorators import account_required, login_required
from ranking_engine import forms
from ranking_engine import models

from django.utils.html import escape
from django.utils import simplejson as json

import logging

import datetime
import calendar

class AddHandler(CommonHandler):

    @login_required
    @account_required
    def get(self, site_key):
        key = db.Key(site_key)
        site = models.Site.get(key)
        if not site:
            self.redirect(self.url("dashboard"))
            return
        if site.account.key() !=  self.account.key():
            self.redirect(self.url("dashboard"))
            return

        if self.account.remaining_keywords() <= 0:
            self.redirect(self.url("site", key = site_key))
            return

        path = os.path.join(TEMPLATES_DIR, 'keyword_add.html')
        template_values = self.get_common_template_values()
        template_values.update({'site' : site,
                                'site_url' : self.url("site", key = site_key),
                                'form' : forms.KeywordForm(),
                                'form_action' : self.url("add_keyword", site_key = site_key)})
        self.response.out.write(template.render(path, template_values))

    @login_required
    @account_required
    def post(self, site_key):
        key = db.Key(site_key)
        site = models.Site.get(key)
        if not site:
            self.redirect(self.url("dashboard"))
            return
        if site.account.key() !=  self.account.key():
            self.redirect(self.url("dashboard"))
            return

        if self.account.remaining_keywords() <= 0:
            self.redirect(self.url("site", key = site_key))
            return

        args = self.request.arguments()
        data = {}
        for i in args:
            if (i == 'server'):
                data[i] = self.request.get_all(i)
            else:
                data[i] = self.request.get(i)

        # instance param looks ugly, but it's the only solution i found to define a parent entity with a form
        form = forms.KeywordForm(data=data,
                                 instance = models.Keyword(parent = site,
                                                           site = site,
                                                           keyword = 'dummy'))
        if form.is_valid():
            keyword = db.run_in_transaction(AddHandler.add_keyword_trx, self, form, site)
            for kw_se in keyword.search_engines():
                kw_se.enqueue_update_rank_task()
            self.redirect(self.url("site", key = site_key))
            return
        else:
            path = os.path.join(TEMPLATES_DIR, 'keyword_add.html')
            template_values = self.get_common_template_values()
            template_values.update({'site' : site,
                                'site_url' : self.url("site", key = site_key),
                                'form' : form,
                                'form_action' : self.url("add_keyword", site_key = site_key)})
            self.response.out.write(template.render(path, template_values))

    def add_keyword_trx(self, form, site):
        keyword = form.save()
        for server in form.cleaned_data['server']:
            kw_se = models.KeywordSearchEngine(parent = keyword,
                                               keyword = keyword,
                                               server = int(server))
            kw_se.put()
        return keyword


class DeleteHandler(CommonHandler):

    @login_required
    @account_required
    def get(self, key):
        key = db.Key(key)
        keyword = models.Keyword.get(key)

        if not keyword:
            self.redirect(self.url("dashboard"))
            return

        site = keyword.site;
        if not site:
            self.redirect(self.url("dashboard"))
            return
        if site.account.key() !=  self.account.key():
            self.redirect(self.url("dashboard"))
            return


        path = os.path.join(TEMPLATES_DIR, 'keyword_delete.html')
        template_values = self.get_common_template_values()
        template_values.update({'keyword' : keyword,
                                'breadcrumb_label' : "Delete keyword " + keyword.keyword,
                                'delete_url' : self.url("delete_keyword", key = key)});
        self.response.out.write(template.render(path, template_values))


    @login_required
    @account_required
    def post(self, key):
        key = db.Key(key)
        keyword = models.Keyword.get(key)

        if not keyword:
            self.redirect(self.url("dashboard"))
            return

        site = keyword.site;
        if not site:
            self.redirect(self.url("dashboard"))
            return
        if site.account.key() !=  self.account.key():
            self.redirect(self.url("dashboard"))
            return

        keyword.delete()
        self.redirect(self.url("site", key = site.key()))



class GraphHandler(CommonHandler):

    @login_required
    @account_required
    def get(self, key):
        key = db.Key(key)
        keyword = models.Keyword.get(key)

        if not keyword:
            self.redirect(self.url("dashboard"))
            return

        site = keyword.site;
        if not site:
            self.redirect(self.url("dashboard"))
            return
        if site.account.key() !=  self.account.key():
            self.redirect(self.url("dashboard"))
            return


        data = []
        for kw_se in keyword.search_engines():
            data.append(kw_se.plot_data())


        today = datetime.datetime.today()
        delta = datetime.timedelta(days=7)
        seven_days_ago = today - delta;
        delta = datetime.timedelta(days=30)
        one_month_ago = today - delta;
        delta = datetime.timedelta(days=180)
        six_months_ago = today - delta


        path = os.path.join(TEMPLATES_DIR, 'keyword_graph.html')
        template_values = self.get_common_template_values()
        template_values.update({'keyword' : keyword,
                                'now' : calendar.timegm(today.timetuple()) * 1000,
                                'seven_days_ago' : calendar.timegm(seven_days_ago.timetuple()) * 1000,
                                'one_month_ago' : calendar.timegm(one_month_ago.timetuple()) * 1000,
                                'six_months_ago' : calendar.timegm(six_months_ago.timetuple()) * 1000,
                                'data' : json.dumps(data)});
        self.response.out.write(template.render(path, template_values))

