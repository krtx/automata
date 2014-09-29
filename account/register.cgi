#! /usr/bin/env ruby
# -*- coding: utf-8 -*-
$KCODE = 'UTF8' if RUBY_VERSION < "1.9"

$:.unshift('./lib')

require 'rubygems'
require 'mail'
require 'webrick'

require 'app'
require 'cgi_helper'
require 'reset'
require 'string/random'

helper = CGIHelper.new
app = App.new(helper.cgi.remote_user)
def app.su?() return true end

class AlreadyRegistered < Exception; end

begin
  email = helper.param(:email)
  user = app.users.find {|u| u.email == email}

  raise AlreadyRegistered if user

  name = helper.param(:name)
  ruby = helper.param(:ruby)
  login = helper.param(:login).to_s

  app.add_user(name, ruby, login, email)

  app.reset(email, :passwd_issue)

  print helper.cgi.header('status' => '303 See Other', 'Location' => '../account/register.html#done')
rescue AlreadyRegistered
  print helper.cgi.header('status' => '303 See Other', 'Location' => '../account/register.html#alreadyregistered')
rescue => e
 print helper.cgi.header('status' => '303 See Other', 'Location' => '../account/register.html#failed')
end
