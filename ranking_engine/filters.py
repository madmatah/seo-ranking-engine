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
register = webapp.template.create_template_register()

@register.filter
def trunc(value, limit):
    """
    Truncate string (see ext.trunc.trunc)
    """
    if len(value) <= limit:
        return value
    else:
        return value[:limit].rsplit(' ', 1)[0]+'...'


@register.filter
def variation(value):
    if (value == None):
        return ""
    elif (value > 0):
        return '<span class="variation positive">+' + unicode(value) + '</span>'
    elif (value < 0):
        return '<span class="variation negative">' + unicode(value) + '</span>'
    else:
        return '<span class="variation null"></span>'
