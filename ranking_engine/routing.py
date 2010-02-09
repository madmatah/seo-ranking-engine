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

def add_routes(map):

    map.connect('home', '/',
                controller = 'handlers.pages:HomeHandler')

    map.connect('terms', '/terms',
                controller = 'handlers.pages:TermsHandler')

    map.connect('dashboard', '/dashboard',
                controller = 'handlers.pages:DashboardHandler')

    map.connect('signup', '/signup',
                controller = 'handlers.pages:SignupHandler')

    map.connect('signup_forbidden', '/signup/forbidden',
                controller = 'handlers.pages:SignupForbiddenHandler')

    map.connect('account_pending', '/account/pending',
                controller = 'handlers.pages:AccountPendingHandler')

    map.connect('add_site', '/site/add',
                controller = 'handlers.sites:AddSiteHandler')

    map.connect('delete_site', '/site/delete/:key',
                controller = 'handlers.sites:DeleteHandler')

    map.connect('site', '/site/:key',
                controller = 'handlers.sites:SiteHandler')

    map.connect('add_keyword', '/keyword/add/:site_key',
                controller = 'handlers.keywords:AddHandler')

    map.connect('delete_keyword', '/keyword/delete/:key',
                controller = 'handlers.keywords:DeleteHandler')

    map.connect("keyword_graph", "/keyword/graph/:key",
                controller = 'handlers.keywords:GraphHandler')
