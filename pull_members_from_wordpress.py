#!./venv/bin/python
import datetime
import xmlrpc.client
import csv
import yaml
import os

with open('config.yaml') as config_f:
    config = yaml.safe_load(config_f)

wp_url = config['wordpress']['url']
wp_username = config['wordpress']['username']
wp_password = config['wordpress']['password']
wp_blogid = "0"

server = xmlrpc.client.ServerProxy(wp_url)
users = server.wp.getUsers(wp_blogid, wp_username, wp_password, {'role':'active_member', 'number':False}, ['nickname','rfid_code'])

with open('%s/members' % os.path.dirname(os.path.realpath(__file__)), "w") as ofile:
    writer = csv.writer(ofile, quoting=csv.QUOTE_NONE)
    for user in users:
        if 'nickname' in user and 'rfid_code' in user:
            if user['nickname'] and user['rfid_code']:
                writer.writerow([user['rfid_code'], user['nickname']])
