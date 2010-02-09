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

from google.appengine.api.labs import taskqueue
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.datastore import entity_pb
import datetime
import calendar
import validators
from routes import url_for
import config
import random

import logging

## See http://blog.notdot.net/2009/9/Efficient-model-memcaching
def serialize_entities(models):
    if models is None:
        return None
    elif isinstance(models, db.Model):
        # Just one instance
        return db.model_to_protobuf(models).Encode()
    else:
        # A list
        return [db.model_to_protobuf(x).Encode() for x in models]

def deserialize_entities(data):
    if data is None:
        return None
    elif isinstance(data, str):
        # Just one instance
        return db.model_from_protobuf(entity_pb.EntityProto(data))
    else:
        return [db.model_from_protobuf(entity_pb.EntityProto(x)) for x in data]


#     @classmethod
#     def get_cached_by_key_name(cls, key_names):
#         """Gets multiple entitites by key name using memcache if available, and 
#         returns a dict key_name:entity.
#         """
#         key_names = set(key_names)

#         # Get all gadget Protocol Buffers from memcache.
#         namespace = cls.__name__
#         pbs = memcache.get_multi(key_names, namespace=namespace)
#         found = [key_name for key_name in key_names if key_name in pbs]

#         # Build a dict with the deserialized entities.
#         res = dict(zip(found, deserialize_entities(pbs[key_name] for key_name in \
#             found)))

#         if len(key_names) != len(found):
#             # Get a list of those not found in memcache, and fetch them.
#             not_found = [key_name for key_name in key_names if key_name not in \
#                 pbs]
#             entities = cls.get_by_key_name(not_found)
#             values = [entity for entity in entities if entity]

#             if values:
#                 keys = [key_name for key_name, entity in zip(not_found, 
#                     entities) if entity]

#                 # Serialize and store the fetched entities in memcache.
#                 memcache.set_multi(dict(zip(keys,
#                     serialize_entities(values))), namespace=namespace)

#                 res.update(dict(zip(keys, values)))
#         return res

class BaseModel(db.Model):

    # See http://code.google.com/p/memcached/wiki/FAQ#Deleting_by_Namespace
    def get_cache_namespace(self):
        final_ns = ""

        # Get the namespace of the parent entity (if specified)
        parent = self.get_cache_parent()
        if parent is not None:
            final_ns += parent.get_cache_namespace()

        # Get the namespace of the current entity
        cache_key = self._get_cache_namespace_key()
        ns = memcache.get(cache_key)
        if ns == None:
            ns = self._init_cache_namespace()
        final_ns += "[NS:" + self.__class__.__name__ + ":" + str(self.key().id_or_name()) + ":" + str(ns) + "]"

        return final_ns

    def update_cache_namespace(self):
        final_ns = ""

        # Get the namespace of the parent entity (if specified)
        parent = self.get_cache_parent()
        if parent is not None:
            final_ns += parent.get_cache_namespace()

        # Get the namespace of the current entity
        cache_key = self._get_cache_namespace_key()
        ns = memcache.incr(cache_key, initial_value = random.randint(1, 1000))
        if ns == None:
            raise Exception("Unable to update cache namespace")
        final_ns += "[NS:Account:" + str(ns) + "]"
        return final_ns

    def _get_cache_namespace_key(self):
        return "NS:" + self.__class__.__name__ + ":" + str(self.key().id_or_name())

    def _init_cache_namespace(self):
        ns_value = random.randint(1, 1000)
        memcache.set(self._get_cache_namespace_key(), ns_value)
        return ns_value

    def get_cache_parent(self):
        return None



class Account(BaseModel):
    user = db.UserProperty(indexed = True)
    created_at = db.DateTimeProperty(required = True, auto_now_add = True)
    last_login = db.DateTimeProperty(indexed = True, auto_now_add = True)
    max_site = db.IntegerProperty(required = True, default = config.max_sites_per_user)
    max_keyword = db.IntegerProperty(required = True, default = config.max_keywords_per_user)
    enabled = db.BooleanProperty(indexed = True)

    def instance_cache_key_by_user(self):
        return Account.cache_key_by_user(self.user)

    @classmethod
    def cache_key_by_user(cls, user):
        return "Account:user:" + user.user_id()

    def delete(self):
        memcache.delete(self.instance_cache_key_by_user())
        Account.cascade_delete(self.key())
        super(Account, self).delete()

    def put(self):
        memcache.delete(self.instance_cache_key_by_user())
        super(Account, self).put()

    @classmethod
    def cascade_delete(cls, key):
        queue = taskqueue.Queue("default")
        task = taskqueue.Task(url = '/tasks/delete/sites', params = {'account_key' : key})
        queue.add(task)

    def remaining_sites(self):
        return self.max_site - len(self.sites())

    def remaining_keywords(self):
        count = 0
        for site in self.sites():
            count += len(site.keywords())
        return (self.max_keyword - count)

    def sites(self):
        ns = self.get_cache_namespace()
        sites = memcache.get('sites', ns)
        if sites is not None:
            return deserialize_entities(sites)
        else:
            sites = Site.all().filter("account =", self).order("label").fetch(1000)
            memcache.set('sites', serialize_entities(sites), namespace = ns)
            return sites

    @classmethod
    def get_user_account(cls, user):
        cache_key = cls.cache_key_by_user(user)
        account = memcache.get(cache_key)
        if account is not None:
            return deserialize_entities(account)
        else:
            account = cls.gql("WHERE user = :user", user = user).get()
            memcache.set(cache_key, serialize_entities(account))
            return account


class Site(BaseModel):
    account = db.ReferenceProperty(reference_class = Account, required = True, indexed = True)
    created_at = db.DateTimeProperty(required = True, auto_now_add = True)
    label = db.StringProperty(required = True, verbose_name = "Name")
    url = db.StringProperty(required = True, verbose_name = "Url", validator = validators.validate_site_url)

    def get_cache_parent(self):
        return self.account

    def put(self):
        self.account.update_cache_namespace()
        super(Site, self).put()

    def delete(self):
        self.account.update_cache_namespace()
        Site.cascade_delete(self.key())
        super(Site, self).delete()

    @classmethod
    def cascade_delete(cls, key):
        queue = taskqueue.Queue("default")
        task = taskqueue.Task(url = '/tasks/delete/keywords', params = {'site_key' : key})
        queue.add(task)

    def keywords(self):
        ns = self.get_cache_namespace()
        keywords = memcache.get('keywords', ns)
        if keywords is not None:
            return deserialize_entities(keywords)
        else:
            keywords = Keyword.all().filter("site =", self).order("keyword").fetch(1000)
            memcache.set('keywords', serialize_entities(keywords), namespace = ns)
            return keywords

    def report_url(self):
        return url_for("site", key = self.key())

    def delete_url(self):
        return url_for("delete_site", key = self.key())


class Keyword(BaseModel):
    site = db.ReferenceProperty(reference_class = Site, indexed = True, required = True)
    created_at = db.DateTimeProperty(required = True, auto_now_add = True)
    keyword = db.StringProperty(required = True, verbose_name = "Keyword", indexed = True)

    def get_cache_parent(self):
        return self.site

    def delete(self):
        self.site.update_cache_namespace()
        Keyword.cascade_delete(self.key())
        super(Keyword, self).delete()

    def put(self):
        self.site.update_cache_namespace()
        super(Keyword, self).put()

    def delete_url(self):
        return url_for("delete_keyword", key = self.key())

    def graph_url(self):
        return url_for("keyword_graph", key = self.key())

    @classmethod
    def cascade_delete(cls, key):
        queue = taskqueue.Queue("default")
        task = taskqueue.Task(url = '/tasks/delete/keyword_search_engines', params = {'keyword_key' : key})
        queue.add(task)

    def search_engines(self):
        ns = self.get_cache_namespace()
        keyword_search_engines = memcache.get('keyword_search_engines', ns)
        if keyword_search_engines is not None:
            return deserialize_entities(keyword_search_engines)
        else:
            keyword_search_engines = KeywordSearchEngine.all().filter("keyword = ", self).order("server").fetch(1000)
            memcache.set('keyword_search_engines', serialize_entities(keyword_search_engines), namespace = ns)
            return keyword_search_engines


class KeywordSearchEngine(BaseModel):
    keyword = db.ReferenceProperty(reference_class = Keyword, indexed = True)
    server = db.IntegerProperty(required = True, verbose_name = "Server", indexed = True)
    created_at = db.DateTimeProperty(required = True, auto_now_add = True)
    last_update = db.DateTimeProperty(indexed = True)

    last_log_entity = None
    variation_cache = None

    def get_cache_parent(self):
        return self.keyword

    def delete(self):
        # Invalidate cache at Site level because of site report (site.html)
        self.keyword.site.update_cache_namespace()
        KeywordSearchEngine.cascade_delete(self.key())
        super(KeywordSearchEngine, self).delete()

    def put(self):
        # Invalidate cache at site level because of site report (site.html)
        self.keyword.site.update_cache_namespace()
        super(KeywordSearchEngine, self).put()

    @classmethod
    def cascade_delete(cls, key):
        queue = taskqueue.Queue("default")
        task = taskqueue.Task(url = '/tasks/delete/keyword_rank_logs', params = {'keyword_se_key' : key})
        queue.add(task)

    def search_engine(self):
        return config.search_engines.get(self.server, None)

    def last_log(self):
        if self.last_log_entity == None:
            self.last_log_entity = KeywordRankLog.all().filter("keyword_se = ", self).order("-date").get()
        return self.last_log_entity

    def full_log(self):
        ns = self.get_cache_namespace()
        rank_logs = memcache.get('full_log', ns)
        if rank_logs is not None:
            return deserialize_entities(rank_logs)
        else:
            rank_logs = KeywordRankLog.all().filter("keyword_se = ", self).order("-date").fetch(1000)
            memcache.set('full_log', serialize_entities(rank_logs), namespace = ns)
            return rank_logs

    def variation(self):
        if self.variation_cache == None:
            query = KeywordRankLog.all().filter("keyword_se = ", self).order("-date")
            if query.count() >= 2:
                set = query.fetch(2)
                yesterday = set[0]
                twodaysago = set[1]
                if twodaysago.rank and yesterday.rank:
                    self.variation_cache = twodaysago.rank - yesterday.rank
        return self.variation_cache


    def enqueue_update_rank_task(self):
        KeywordSearchEngine.enqueue_update_rank_task_key(unicode(self.key()))

    @classmethod
    def enqueue_update_rank_task_key(cls, key):
        se_calls_queue = taskqueue.Queue("search-engine-calls")
        task = taskqueue.Task(url = '/tasks/update_keyword_se_rank', params = {'key': key})
        se_calls_queue.add(task)

    def plot_data(self):
        data = []
        for log in self.full_log():
            log_ts = calendar.timegm(log.date.timetuple()) * 1000
            log_rank = log.rank
            data.append([log_ts, log_rank])
        return {'data': data, 'label': self.search_engine()['label']}


class KeywordRankLog(BaseModel):
    keyword_se = db.ReferenceProperty(reference_class = KeywordSearchEngine, indexed = True)
    date = db.DateTimeProperty(auto_now_add = True, required = True, indexed = True)
    rank = db.IntegerProperty()
    url = db.StringProperty()
    total = db.IntegerProperty()

    def get_cache_parent(self):
        return self.keyword_se

    def delete(self):
        self.keyword_se.update_cache_namespace()
        super(KeywordRankLog, self).delete()

    def put(self):
        self.keyword_se.update_cache_namespace()
        super(KeywordRankLog, self).put()

