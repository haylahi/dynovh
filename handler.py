#!/usr/bin/python
# coding=utf-8

# Copyright 2014 Hubert Godfroy

# This file is part of dynovh.

# dynovh is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# dynovh is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with dynovh.  If not, see <http://www.gnu.org/licenses/>


import OvhApi
import key
import urllib2, time, re, sys, xmlrpclib

__author__ = 'hubert'

#REFIP = 'checkip.dyndns.com'
REFIP = 'checkip.pointfixe.fr'
NBR_CONNEXION = 10
NBR_ATTEMPT_REFIP = 10

key = key.key()
AK = key.appkey
AS = key.appsec
CK = key.conkey

api = OvhApi.Api("https://eu.api.ovh.com/1.0", AK, AS, CK)

def get_zone_id(zone):
  res = api.get('/domain/zone/' + zone[0] + '/record?fieldType=A&subDomain=' + zone[1])
  if not isinstance(res, list):
    raise Exception(str(res))
  if len(res) == 0:
    raise Exception("Le nom de domaine " + zone[0] + " ne contient pas de sous-domaine " + zone[1])
  return res[0]

def update_zone(zone_name, zone_id, new_ip):
  new = {u'target': new_ip, 'fieldType': 'A', 'ttl': 300}
  return (api.put('/domain/zone/' + zone_name + '/record/' + str(zone_id), new))

def refresh_zone(zone_name):
    return (api.post('/domain/zone/' + zone_name + '/refresh', {}))

def get_old_ip(zone_name, zone_id):
  res = api.get('/domain/zone/' + zone_name + '/record/' + str(zone_id))
  try:
    oldip = res["target"]
  except:
    raise Exception(str(res))
  return oldip

def get_current_ip():
    i = 0
    succed = False
    while not succed:
        if i >= NBR_ATTEMPT_REFIP :
            raise Exception("Impossion de trouver l'ip courante")
        try:
            #f = urllib2.urlopen('http://' + REFIP, None, 10)
            import socket
            host = socket.gethostbyname(REFIP)
            request = urllib2.Request('http://{}'.format(host), headers = {'Host': REFIP})
            f = urllib2.urlopen(request)
            succed = True
        except:
            succed = False
            i = i + 1
    data = f.read()
    f.close()
    pattern = re.compile('\d+\.\d+\.\d+\.\d+')
    result = pattern.search(data, 0)
    if result == None:
        raise Exception("Pas d'ip dans cette page")
        sys.exit()
    else:
        currentip = result.group(0)
        #print(currentip)
    return currentip

def process_zone(dyndoms, forced_ip = None):
  current_ip = ''
  if forced_ip == None:
      current_ip = get_current_ip()
  else:
      current_ip = forced_ip
  for zone in dyndoms:
    zone_id = get_zone_id(zone)
    zone_name = zone[0]
    old_ip = get_old_ip(zone_name, zone_id)
    report = 'zone ' + zone[1] + '.' + zone_name
    report = report + "\n" + old_ip
    report = report + "\n" + current_ip

    if old_ip != current_ip:
      ret = update_zone(zone_name, zone_id, current_ip)
      if ret != None:
        raise Exception(str(ret))
      ret = refresh_zone(zone_name)
      if ret != None:
        raise Exception(str(ret))
      print(report)
      print("Modification de l'enregistrement effectuée avec l'ip: %s" % current_ip)
