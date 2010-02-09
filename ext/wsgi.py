#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# http://www.apache.org/licenses/LICENSE-2.0
#

import sys
from google.appengine.ext.webapp import Request
from google.appengine.ext.webapp import Response
from routes.util import URLGenerator

class WSGIApplication(object):
    """Wraps a set of webapp RequestHandlers in a WSGI-compatible application.
    This is based on webapp's WSGIApplication by Google, but uses Routes library
    (http://routes.groovie.org/) to match url's.
    """
    def __init__(self, mapper, debug = False):
        """Initializes this application with the given URL mapping.
        Args:
          mapper: a routes.mapper.Mapper instance
          debug: if true, we send Python stack traces to the browser on errors
        """
        self.mapper = mapper
        self.__debug = debug
        WSGIApplication.active_instance = self
        self.current_request_args = ()
    def __call__(self, environ, start_response):
        """Called by WSGI when a request comes in."""

        url = URLGenerator(self.mapper, environ)
        environ['routes.url'] = url

        request = Request(environ)
        response = Response()
        WSGIApplication.active_instance = self
        # Match the path against registered routes.
        kargs = self.mapper.match(request.path)
        if kargs is None:
            raise TypeError('No routes match. Provide a fallback to avoid this.')
        # Extract the module and controller names from the route.
        try:
            module_name, class_name = kargs['controller'].split(':', 1)
            del kargs['controller']
        except:
            raise TypeError('Controller is not set, or not formatted in the form "my.module.name:MyControllerName".')
        # Initialize matched controller from given module.
        try:
            __import__(module_name)
            module = sys.modules[module_name]
            controller = getattr(module, class_name)()
            controller.initialize(request, response)
        except:
            raise ImportError('Controller %s from module %s could not be initialized.' % (class_name, module_name))
        # Use the action set in the route, or the HTTP method.
        if 'action' in kargs:
            action = kargs['action']
            del kargs['action']
        else:
            action = environ['REQUEST_METHOD'].lower()
            if action not in ['get', 'post', 'head', 'options', 'put', 'delete', 'trace']:
                action = None
        if controller and action:
            try:
                # Execute the requested action, passing the route dictionary as
                # named parameters.
                getattr(controller, action)(**kargs)
            except Exception, e:
                controller.handle_exception(e, self.__debug)
            response.wsgi_write(start_response)
            return ['']
        else:
            response.set_status(404)
