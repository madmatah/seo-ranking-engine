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
from routes import url_for

from django import template
from django.template import loader, Node
from django.template import VariableDoesNotExist
from django.template import resolve_variable
from django.utils.html import escape

import logging

register = webapp.template.create_template_register()

@register.tag
def url(parser, token):
    return UrlNode(token.split_contents()[1:])


class UrlNode(Node):
	def __init__(self, vars):
		"""
		First var is title, second var is url context variable
		"""
		self.vars = vars

	def render(self, context):
		title = resolve_variable(self.vars[0], context)

		if title.find("'")==-1 and title.find('"')==-1:
			try:
                            title = resolve_variable(self.vars[0], context)
			except:
                            title = ''

		else:
			title=title.strip("'").strip('"')
			title=unicode(title)

                return url_for(title)


@register.tag
def breadcrumb(parser, token):
	"""
	Renders the breadcrumb.
	Examples:
		{% breadcrumb "Title of breadcrumb" url_var %}
		{% breadcrumb context_var  url_var %}
		{% breadcrumb "Just the title" %}
		{% breadcrumb just_context_var %}

	Parameters:
	-First parameter is the title of the crumb,
	-Second (optional) parameter is the url variable to link to, produced by url tag, i.e.:
		{% url person_detail object.id as person_url %}
		then:
		{% breadcrumb person.name person_url %}

	@author Andriy Drozdyuk
	"""
	return BreadcrumbNode(token.split_contents()[1:])


@register.tag
def breadcrumb_url(parser, token):
	"""
	Same as breadcrumb
	but instead of url context variable takes in all the
	arguments URL tag takes.
		{% breadcrumb "Title of breadcrumb" person_detail person.id %}
		{% breadcrumb person.name person_detail person.id %}
	"""

	bits = token.split_contents()
	if len(bits)==2:
		return breadcrumb(parser, token)

	# Extract our extra title parameter
	title = bits.pop(1)
	token.contents = ' '.join(bits)

	url = bits.pop(1)

	return UrlBreadcrumbNode(title, url)

@register.tag
def breadcrumb_route(parser, token):
	"""
	Same as breadcrumb
	but instead of url context variable takes in all the
	arguments URL tag takes.
		{% breadcrumb "Title of breadcrumb" person_detail person.id %}
		{% breadcrumb person.name person_detail person.id %}
	"""

	bits = token.split_contents()
	if len(bits)==2:
		return breadcrumb(parser, token)

	# Extract our extra title parameter
	title = bits.pop(1)
	token.contents = ' '.join(bits)

	url = bits.pop(1)

	return RouteBreadcrumbNode(title, url)


class BreadcrumbNode(Node):
	def __init__(self, vars):
            """
            First var is title, second var is url context variable
            """
            self.vars = vars

	def render(self, context):
            title = resolve_variable(self.vars[0], context)

            if title.find("'")==-1 and title.find('"')==-1:
                try:
                    title = resolve_variable(self.vars[0], context)
                except:
                    title = ''
            else:
                title=title.strip("'").strip('"')
                title=unicode(title)

            url = None
            if len(self.vars)>1:
                val = self.vars[1]
                try:
                    url = val.resolve(context)
                except VariableDoesNotExist:
                    print 'URL does not exist', val
                    url = None
            return create_crumb(title, url)

class UrlBreadcrumbNode(Node):
    def __init__(self, title, url):
        self.title = title
        self.url = url

    def render(self, context):
        title = resolve_variable(self.title, context)
        if title.find("'")==-1 and title.find('"')==-1:
            try:
                title = resolve_variable(self.title, context)
            except:
                title = ''
        else:
            title=title.strip("'").strip('"')
            title=unicode(title)

        url = resolve_variable(self.url, context)
        if url.find("'") == -1 and title.find('"') == -1:
            try:
                url = resolve_variable(self.url, context)
            except:
                url = None
        else:
            url = url.strip("'").strip('"')
            url = unicode(url)

        return create_crumb(title, url)


class RouteBreadcrumbNode(Node):
    def __init__(self, title, url):
        self.title = title
        self.url = url

    def render(self, context):
        title = resolve_variable(self.title, context)
        if title.find("'")==-1 and title.find('"')==-1:
            try:
                title = resolve_variable(self.title, context)
            except:
                title = ''
        else:
            title=title.strip("'").strip('"')
            title=unicode(title)

        url = resolve_variable(self.url, context)
        if url.find("'") == -1 and title.find('"') == -1:
            try:
                url = resolve_variable(self.url, context)
            except:
                url = None
        else:
            url = url.strip("'").strip('"')
            url = unicode(url)

        if (url):
            url = url_for(url)
        return create_crumb(title, url)


def create_crumb(title, url=None):
	"""
	Helper function
	"""
	if url:
            crumb = u"&nbsp;<a href='%s'>%s</a>" % (escape(url), escape(title))
	else:
            crumb = u"&nbsp;<span>%s</span>" % (escape(title))
	return crumb
