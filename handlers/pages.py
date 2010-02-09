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
import time
import datetime

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext.db import djangoforms
from google.appengine.ext import db
from google.appengine.api import memcache

import datetime

from ranking_engine.decorators import account_required, login_required

from ranking_engine import forms
from ranking_engine import models
import config

import logging

class CommonHandler(webapp.RequestHandler):

    account = None;

    def url(self, *args, **kargs):
        return self.request.environ['routes.url'](*args, **kargs)

    def get_common_template_values(self):

        return({
                'user' : users.get_current_user(),
                'is_admin' : users.is_current_user_admin(),
                'account' : self.account,
                'login_url' : users.create_login_url(self.url("dashboard")),
                'logout_url' : users.create_logout_url(self.url("home")),
                'url' : self.request.environ['routes.url'],
                'is_xhr' : self.request.headers.get('X_REQUESTED_WITH') == 'XMLHttpRequest'
                })

    def get_account(self):
        if not self.account:
            user = users.get_current_user()
            if (user):
                self.account = models.Account.get_user_account(user)
                if self.account and not self.account.enabled:
                    self.redirect(self.url("account_pending"))
                    return
                if self.account:
                    # Track last_login date every hour (to avoid saving it on each request)
                    last_login_cache_key = "Last_login:" + unicode(self.account.key())
                    last_login_delta = 3600;
                    if memcache.get(last_login_cache_key) == None:
                        self.account.last_login = datetime.datetime.now()
                        self.account.put()
                        memcache.set(last_login_cache_key, "ok", last_login_delta)
        return self.account

class HomeHandler(CommonHandler):

    def get(self):
        user = users.get_current_user()
        if not user:
            path = os.path.join(config.TEMPLATES_DIR, 'home.html')
            template_values = self.get_common_template_values()
            self.response.out.write(template.render(path, template_values))
        else:
            self.redirect(self.url("dashboard"))
            return


class SignupHandler(CommonHandler):

    @login_required
    def get(self):

        # If account exists, redirect user to the dashboard
        account = self.get_account()
        if (account):
            self.redirect(self.url("dashboard"))
            return

        if config.admin_only and not users.is_current_user_admin():
            self.redirect(users.create_logout_url(self.url("signup_forbidden")))
            return

        path = os.path.join(config.TEMPLATES_DIR, 'signup.html')
        template_values = self.get_common_template_values()
        template_values.update({'form_action' : self.request.uri});
        self.response.out.write(template.render(path, template_values))

    def post(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
            return
        account = self.get_account()
        if (account):
            self.redirect(self.url("dashboard"))
            return

        if config.admin_only and not users.is_current_user_admin():
            self.redirect(self.url("home"))
            return

        if not self.request.get('accept_terms'):
            path = os.path.join(config.TEMPLATES_DIR, 'signup.html')
            template_values = self.get_common_template_values()
            template_values.update({'form_action' : self.url("signup"),
                                    'form_error' : 'You must read and agree the terms of service to create an account'});
            self.response.out.write(template.render(path, template_values))
            return
        else:
            account = models.Account()
            account.user = user
            if config.moderate_signups and not users.is_current_user_admin():
                account.enabled = False
            else:
                account.enabled = True
            account.put()
            self.redirect(self.url("dashboard"))
            return

class TermsHandler(CommonHandler):
    def get(self):
        path = os.path.join(config.TEMPLATES_DIR, 'terms.html')
        template_values = self.get_common_template_values()
        self.response.headers.add_header('Content-Type', 'text/plain')
        self.response.out.write(template.render(path, template_values))
        return


class SignupForbiddenHandler(CommonHandler):
    def get(self):
        path = os.path.join(config.TEMPLATES_DIR, 'signup_forbidden.html')
        template_values = self.get_common_template_values()
        self.response.out.write(template.render(path, template_values))
        return


class AccountPendingHandler(CommonHandler):

    @login_required
    def get(self):
        user = users.get_current_user()
        account = models.Account.get_user_account(user)
        if not account:
            self.redirect(self.url("signup"))
            return
        if account.enabled:
            self.redirect(self.url("home"))
            return

        path = os.path.join(config.TEMPLATES_DIR, 'account_pending.html')
        template_values = self.get_common_template_values()
        self.response.out.write(template.render(path, template_values))


class DashboardHandler(CommonHandler):

    @login_required
    @account_required
    def get(self):
        ns = self.account.get_cache_namespace()
        output = memcache.get('dashboard.html', ns)
        if output == None:
            path = os.path.join(config.TEMPLATES_DIR, 'dashboard.html')
            template_values = self.get_common_template_values()
            template_values.update({'sites' : self.account.sites(),
                                    'add_site_url' : self.url('add_site'),
                                    'remaining_sites' : self.account.remaining_sites()});
            output = template.render(path, template_values)
            memcache.set('dashboard.html', output, namespace = ns)
        self.response.out.write(output)

