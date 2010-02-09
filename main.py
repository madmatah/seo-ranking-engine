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
use_library('django', '1.1')

import os

from google.appengine.ext.webapp.util import run_wsgi_app
from ext.wsgi import WSGIApplication

from routes.mapper import Mapper
from ranking_engine.routing import add_routes

from google.appengine.ext.webapp import template


from handlers import pages

def main():
  template.register_template_library('ranking_engine.filters')
  template.register_template_library('ranking_engine.tags')

  map = Mapper(explicit = True)
  add_routes(map)
  application = WSGIApplication(map, debug=True)
  run_wsgi_app(application)

if __name__ == '__main__':
  main()
