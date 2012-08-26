#!/usr/bin/env python
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

from google.appengine.dist import use_library
use_library('django', '1.2')

import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from handlers import tasks

def main():
    application = webapp.WSGIApplication([('/tasks/update_ranks', tasks.UpdateRanksHandler),
                                          ('/tasks/update_keyword_se_rank', tasks.UpdateKeywordSearchEngineRanksHandler),
                                          ('/tasks/delete/sites', tasks.DeleteSitesHandler),
                                          ('/tasks/delete/old_logs', tasks.DeleteOldLogsHandler),
                                          ('/tasks/delete/inactive_accounts', tasks.DeleteInactiveAccountsHandler),
                                          ('/tasks/delete/keywords', tasks.DeleteKeywordsHandler),
                                          ('/tasks/delete/keyword_search_engines', tasks.DeleteKeywordSearchEnginesHandler),
                                          ('/tasks/delete/keyword_rank_logs', tasks.DeleteKeywordRankLogsHandler)],
                                         debug=True)
    run_wsgi_app(application)
if __name__ == "__main__":
    main()


