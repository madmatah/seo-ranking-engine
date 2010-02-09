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

import urllib
import re
import time
import config
from django.utils import simplejson as json
from utils import urlfetch_with_cache

import random
import logging

# Fetch ranking of an URL (url) for a specific keyword (keyword) and search engine (server)
def get_ranking(url, keyword, server):
    server_info = config.search_engines.get(server, None)
    if not server_info:
        raise Exception("Server <" + unicode(server) + "> not found in configured config.search_engines")

    methods = {
        'google-ajax-api' : _google_ajax_api_ranking,
        'yahoo-boss' : _yahoo_boss_ranking,
        'bing-api' : _bing_api_ranking,
        }
    method = methods.get(server_info['type'])
    if not method:
        raise Exception("Unsupported ranking method <" + server_info['type'] + ">. Check your config.py file.")
    result = methods[server_info['type']](url, keyword, server_info)
    return result



# Fetch ranking with google AJAX Search API
def _google_ajax_api_ranking(url, keyword, server_info):
    url_regex = re.compile("^" + url)
    rank_infos = {}
    counter = 0

    base_api_url = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&'

    # Set API Key if defined
    try:
        if config.google_ajax_api_key:
            base_api_url += "key=" + urllib.quote_plus(config.google_ajax_api_key) + "&"
    except:
        pass

    # Set country param
    base_api_url += "gl=" + server_info['gl'] + "&"

    # Each call to google AJAX Search API returns 4 results.
    # We are allowed to fetch 64 results (16 pages)
    num = 4
    for i in range(0, 16):
        start = i * num
        api_url = base_api_url + "start=" + unicode(start) + "&q=" +  urllib.quote_plus(keyword)
        result = urlfetch_with_cache(api_url, 3600, 600)
        if result.status_code != 200:
            raise Exception("Invalid response (url = <" + google_url + ">, status code = " + unicode(result.status_code) + " and content = <" + unicode(result.content) + ">")
        response = json.loads(result.content)
        if response.get('responseData'):
            if i == 0:
                try:
                    rank_infos['total'] = long(response['responseData']['cursor'].get('estimatedResultCount'))
                except:
                    rank_infos['total'] = None
            results = response['responseData'].get('results')
            if results:
                for r in results:
                    counter += 1
                    if (url_regex.match(r['unescapedUrl'])):
                        rank_infos['rank'] = counter
                        rank_infos['url'] = r['unescapedUrl']
                        return  rank_infos
    return rank_infos



# Fetch ranking with Yahoo Search BOSS
def _yahoo_boss_ranking(url, keyword, server_info):
    url_regex = re.compile("^" + url)
    rank_infos = {}
    counter = 0

    base_api_url = 'http://boss.yahooapis.com/ysearch/web/v1/'

    # Set keyword
    base_api_url += urllib.quote_plus(keyword) + '?'

    # Set AppID
    base_api_url += "appid=" + urllib.quote_plus(config.yahoo_boss_appid) + "&"

    # Set Format + Style
    base_api_url += "format=json&style=raw&"

    # Set language and region
    base_api_url += "lang=" + server_info['lang'] + "&region=" + server_info['region'] + "&"

    # Fetch 2x50 results and try to match url
    num = 50
    for i in range(0, 2):
        start = i * num
        api_url = base_api_url + "start=" + unicode(start) + "&count=" +  unicode(num)
        result = urlfetch_with_cache(api_url, 3600, 600)
        if result.status_code != 200:
            raise Exception("Invalid response (url = <" + google_url + ">, status code = " + unicode(result.status_code) + " and content = <" + unicode(result.content) + ">")
        response = json.loads(result.content)
        if response.get('ysearchresponse'):
            if i == 0:
                rank_infos['total'] = long(response['ysearchresponse'].get('totalhits'))
            results = response['ysearchresponse'].get('resultset_web')
            if results:
                for r in results:
                    counter += 1
                    if (url_regex.match(r['url'])):
                        rank_infos['rank'] = counter
                        rank_infos['url'] = r['url']
                        return  rank_infos
    return rank_infos


# Fetch ranking with Bing API
def _bing_api_ranking(url, keyword, server_info):
    url_regex = re.compile("^" + url)
    rank_infos = {}
    counter = 0

    base_api_url = 'http://api.bing.net/json.aspx?Version=2.2&Sources=web&JsonType=raw&'

    # Set AppID
    base_api_url += "AppId=" + urllib.quote_plus(config.bing_appid) + "&"

    # Set Market (language-region)
    base_api_url += "Market=" + server_info['market'] + "&"

    # Set keyword
    base_api_url += "Query=" + urllib.quote_plus(keyword) + "&"

    # Fetch 2x50 results and try to match url
    num = 50
    for i in range(0, 2):
        start = i * num
        api_url = base_api_url + "Web.offset=" + unicode(start) + "&Web.count=" +  unicode(num)
        result = urlfetch_with_cache(api_url, 3600, 600)
        if result.status_code != 200:
            raise Exception("Invalid response (url = <" + google_url + ">, status code = " + unicode(result.status_code) + " and content = <" + unicode(result.content) + ">")
        response = json.loads(result.content)
        if response.get('SearchResponse'):
            web = response['SearchResponse'].get('Web')
            if web:
                if i == 0:
                    rank_infos['total'] = long(web.get('Total'))
                results = web.get('Results')
                if results:
                    for r in results:
                        counter += 1
                        if (url_regex.match(r['Url'])):
                            rank_infos['rank'] = counter
                            rank_infos['url'] = r['Url']
                            return  rank_infos
    return rank_infos

