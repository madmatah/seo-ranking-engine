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

from google.appengine.ext import db
import urlparse

def validate_site_url(url):
    u = urlparse.urlparse(url)
    if (u.scheme != 'http' and u.scheme != 'https'):
        raise db.BadValueError('Invalid URL : the scheme must be HTTP or HTTPS')

    if (u.scheme == 'http' and u.port and u.port != 80):
        raise db.BadValueError('You must use standard ports (80 for HTTP)')

    if (u.scheme == 'https' and u.port and u.port != 443):
        raise db.BadValueError('You must use standard ports (443 for HTTPS)')

    return (url)

