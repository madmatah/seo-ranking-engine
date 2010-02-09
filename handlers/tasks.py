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

from google.appengine.ext import webapp
from google.appengine.api.labs import taskqueue
from google.appengine.ext import db

import datetime
import time
import logging

from ranking_engine import models
from ranking_engine import ranking
import config


class UpdateRanksHandler(webapp.RequestHandler):

    """ Cron job launched every 24 hours
    It just launch a loop task to process all keywords """
    def get(self, *ar, **kw):
        default_queue = taskqueue.Queue("default")
        task = taskqueue.Task(url='/tasks/update_ranks', params= {'time': time.time()})
        default_queue.add(task)


    def post(self, *ar, **kw):
        time = self.request.get('time')

        today = datetime.date.today()
        if not time or datetime.date.fromtimestamp(float(time)) < today:
            logging.info("Ignoring deprecated task UpdateRanksHandler:post(time = " + time + ")")
            return

        last_key = self.request.get('last_key')
        if not last_key:
            query = db.GqlQuery('SELECT __key__ FROM KeywordSearchEngine ORDER BY __key__')
        else:
            query = db.GqlQuery('SELECT __key__ FROM KeywordSearchEngine WHERE __key__ > :last_key ORDER BY __key__',
                                last_key = db.Key(last_key))
        entities = query.fetch(100)
        if entities:
            default_queue = taskqueue.Queue("default")
            se_calls_queue = taskqueue.Queue("search-engine-calls")
            for key in entities:
                task = taskqueue.Task(url = '/tasks/update_keyword_se_rank', params = {'key': key})
                se_calls_queue.add(task)
                last_key = key
            task = taskqueue.Task(url = '/tasks/update_ranks',
                                  params = {'time': time, 'last_key' : last_key})
            default_queue.add(task)


class UpdateKeywordSearchEngineRanksHandler(webapp.RequestHandler):

    def update_trx(self, kw_se, result):
        # Insert KeywordRankLog
        rankLog = models.KeywordRankLog(parent = kw_se)
        rankLog.keyword_se = kw_se
        if result and result.get('rank'):
            rankLog.rank = result.get('rank')
            rankLog.url = result.get('url')
            rankLog.total = result.get('total')
        rankLog.put()

        # Update kw_se.last_update
        kw_se.last_update = datetime.datetime.today()
        kw_se.put()
        return

    def post(self, *ar, **kw):
        key = self.request.get('key')

        kw_se = models.KeywordSearchEngine.get(db.Key(key))
        if not kw_se:
            logging.warning("[UpdateKeywordSearchEngineRanksHandler] Ignoring task, unknown Kw_Se with key <" + key + ">");
            return

        if kw_se.last_update and kw_se.last_update.date() >= datetime.date.today():
            logging.info("[UpdateKeywordSearchEngineRanksHandler] Ignoring task, kw_se <" + key + "> is up to date");

        site = kw_se.keyword.site;
        if not site:
            logging.warning("[UpdateKeywordSearchEngineRanksHandler] Ignoring task: Keyword with key <" + unicode(kw_se.keyword.key()) + "> has no site !");
            return

        # Fetch Search Engine Results
        result = ranking.get_ranking(site.url, kw_se.keyword.keyword, kw_se.server)

        db.run_in_transaction(UpdateKeywordSearchEngineRanksHandler.update_trx,
                              self, kw_se, result)



# Cascade delete on Site when deleting an Account
class DeleteSitesHandler(webapp.RequestHandler):
    def post(self, *ar, **kw):
        key = self.request.get('account_key')
        batch_size = 10
        query = models.Site.all(keys_only=True).filter('account = ', db.Key(key))
        count = query.count()
        site_keys = query.fetch(batch_size)
        for site_key in site_keys:
            models.Site.cascade_delete(site_key)
        db.delete(site_keys)
        if count > batch_size:
            queue = taskqueue.Queue("default")
            task = taskqueue.Task(url = '/tasks/delete/sites', params = {'account_key' : key })
            queue.add(task)


# Cascade delete on Keyword when deleting a Site
class DeleteKeywordsHandler(webapp.RequestHandler):
    def post(self, *ar, **kw):
        key = self.request.get('site_key')
        batch_size = 10
        query = models.Keyword.all(keys_only=True).filter('site = ', db.Key(key))
        count = query.count()
        kw_keys = query.fetch(batch_size)
        for kw_key in kw_keys:
            models.Keyword.cascade_delete(kw_key)
        db.delete(kw_keys)
        if count > batch_size:
            queue = taskqueue.Queue("default")
            task = taskqueue.Task(url = '/tasks/delete/keywords', params = {'site_key' : key })
            queue.add(task)

# Cascade delete on KeywordSearchEngine when deleting a Keyword
class DeleteKeywordSearchEnginesHandler(webapp.RequestHandler):
    def post(self, *ar, **kw):
        key = self.request.get('keyword_key')
        batch_size = 10
        query = models.KeywordSearchEngine.all(keys_only = True).filter('keyword = ', db.Key(key))
        count = query.count()
        kw_se_keys = query.fetch(batch_size)
        for kw_se_key in kw_se_keys:
            models.KeywordSearchEngine.cascade_delete(kw_se_key)
        db.delete(kw_se_keys)
        if count > batch_size:
            queue = taskqueue.Queue("default")
            task = taskqueue.Task(url = '/task/delete/keyword_search_engines', params = {'keyword_key' : key})
            queue.add(task)

# Cascade delete on KeywordRankLog when deleting a Keyword Search Engine
class DeleteKeywordRankLogsHandler(webapp.RequestHandler):
    def post(self, *ar, **kw):
        key = self.request.get('keyword_se_key')
        batch_size = 10
        query = models.KeywordRankLog.all(keys_only=True).filter('keyword_se = ', db.Key(key))
        count = query.count()
        db.delete(query.fetch(batch_size))
        if count > batch_size:
            queue = taskqueue.Queue("default")
            task = taskqueue.Task(url = '/tasks/delete/keyword_rank_logs', params = {'keyword_se_key' : key })
            queue.add(task)


# Remove old rank logs
class DeleteOldLogsHandler(webapp.RequestHandler):

    """ Cron job launched every 24 hours
    It just launch a loop task to delete RankLogs older than config.data_retention_days days """
    def get(self, *ar, **kw):
        if not config.data_retention_days:
            return
        default_queue = taskqueue.Queue("default")
        task = taskqueue.Task(url='/tasks/delete/old_logs')
        default_queue.add(task)

    def post(self,  *ar, **kw):
        if not config.data_retention_days:
            return
        batch_size = 10
        retention_delta = datetime.timedelta(days = config.data_retention_days)
        date = datetime.datetime.today() - retention_delta;
        query = models.KeywordRankLog.all(keys_only=True).filter('date < ', date)
        count = query.count()
        db.delete(query.fetch(batch_size))
        if count > batch_size:
            queue = taskqueue.Queue("default")
            task = taskqueue.Task(url = '/tasks/delete/old_logs')
            queue.add(task)


class DeleteInactiveAccountsHandler(webapp.RequestHandler):

    """ Cron job launched every 24 hours
    It launch a loop task to delete inactive Accounts according to config.max_inactive_account_days """
    def get(self, *ar, **kw):
        if not config.max_inactive_account_days:
            return
        default_queue = taskqueue.Queue("default")
        task = taskqueue.Task(url='/tasks/delete/inactive_accounts')
        default_queue.add(task)

    def post(self,  *ar, **kw):
        if not config.max_inactive_account_days:
            return
        batch_size = 10
        inactivity_delta = datetime.timedelta(days = config.max_inactive_account_days)
        date = datetime.datetime.today() - inactivity_delta;

        query = models.Account.all(keys_only=True).filter('last_login < ', date)
        count = query.count()
        account_keys = query.fetch(batch_size)
        for account_key in account_keys:
            models.Account.cascade_delete(account_key)
        db.delete(account_keys)
        if count > batch_size:
            queue = taskqueue.Queue("default")
            task = taskqueue.Task(url = '/task/delete/inactive_accounts')
            queue.add(task)
