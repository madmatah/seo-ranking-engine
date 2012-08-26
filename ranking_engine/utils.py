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

from google.appengine.api import memcache
from google.appengine.api import urlfetch
import logging
import md5


# URL fetcher function with caching system
def urlfetch_with_cache(url, time, fail_time, headers = {}):
    logging.info("urlfetch_with_cache(<" + unicode(url) + ">, " + unicode(time) + ", " +  unicode(fail_time) + ")")
    digest = md5.md5()
    digest.update('urlfetch:GET:' + url)
    cache_key = digest.hexdigest()

    data = memcache.get(cache_key)
    if data is not None:
        return data
    else:
        data = urlfetch.fetch(url, headers = headers)
        if data.status_code == 200:
            cache_time = time
        else:
            cache_time = fail_time
        cached_data = {
            'status_code': data.status_code,
            'content': data.content
        }
        memcache.add(cache_key, cached_data, cache_time)
        return cached_data
