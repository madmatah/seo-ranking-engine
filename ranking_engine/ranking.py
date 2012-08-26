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
import base64
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
        api_url = base_api_url + "start=" + unicode(start) + "&q=" +  urllib.quote_plus(keyword.encode("UTF-8"))
        result = urlfetch_with_cache(api_url, 3600, 600)
        if result['status_code'] != 200:
            raise Exception("Invalid response (url = <" + google_url + ">, status code = " + unicode(result['status_code']) + " and content = <" + unicode(result['content']) + ">")
        response = json.loads(result['content'])
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


# Fetch ranking with Bing API
def _bing_api_ranking(url, keyword, server_info):
    url_regex = re.compile("^" + url)
    rank_infos = {}
    counter = 0

    base_api_url = 'https://api.datamarket.azure.com/Data.ashx/Bing/SearchWeb/v1/Web?'

    # Set format
    base_api_url += "$format=json&"

    # Set Market (language-region)
    base_api_url += "Market=%27" + server_info['market'] + "%27&"

    # Set keyword
    base_api_url += "Query=%27" + urllib.quote_plus(keyword.encode("UTF-8")) + "%27&"


    # Setup basic authentication
    headers = {
        "Authorization": "Basic %s" % base64.b64encode(":" + config.azure_account_id)
    }
    logging.info(headers)

    # Fetch 2x50 results and try to match url
    num = 50
    for i in range(0, 2):
        start = i * num
        api_url = base_api_url + "$skip=" + unicode(start) + "&$top=" +  unicode(num)
        result = urlfetch_with_cache(api_url, 3600, 600, headers)
        if result['status_code'] != 200:
            raise Exception("Invalid response (url = <" + api_url + ">, status code = " + unicode(result['status_code']) + " and content = <" + unicode(result['content']) + ">")
        response = json.loads(result['content'])
        logging.info(response)
        if response.get('d'):
            results = response['d'].get('results')
            if results:
                # Total number of results is not available anymore via the API
                rank_infos['total'] = None
                for r in results:
                    logging.info(r)
                    counter += 1
                    if (url_regex.match(r['Url'])):
                        rank_infos['rank'] = counter
                        rank_infos['url'] = r['Url']
                        return  rank_infos
    return rank_infos

