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

from google.appengine.api import users

def account_required(handler_method):

    def check_account(self, *args, **kargs):
        account = self.get_account()
        if not account:
            self.redirect(self.url("signup"))
            return
        else:
            handler_method(self, *args, **kargs)

    return check_account


def login_required(handler_method):
  """A decorator to require that a user be logged in to access a handler.

  To use it, decorate your get() method like this:

    @login_required
    def get(self):
      user = users.get_current_user(self)
      self.response.out.write('Hello, ' + user.nickname())

  We will redirect to a login page if the user is not logged in. We always
  redirect to the request URI, and Google Accounts only redirects back as a GET
  request, so this should not be used for POSTs.
  """
  def check_login(self, *args, **kargs):
    user = users.get_current_user()
    if not user:
        if self.request.method != 'GET':
            callback = self.url('home')
        else:
            callback = self.request.uri
        self.redirect(users.create_login_url(callback))
        return
    else:
        handler_method(self, *args, **kargs)
  return check_login
