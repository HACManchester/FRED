#!./venv/bin/python
import serial
import sys
import logging
import paho.mqtt.client as mqtt
import yaml
import requests
import json

with open('config.yaml') as config_f:
    config = yaml.safe_load(config_f)

ser = serial.Serial(config['serial']['port'], config['serial']['baud'], timeout=0.5)

# We want to use a logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(message)s')

# Anything DEBUG or higher should be logged to disk
fh = logging.FileHandler('fred.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

# Anything DEBUG or higher should be spat out to the console
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)

logging.info("FRED 1.0")

mqttc = mqtt.Client(config['mqtt']['name'])
mqttc.will_set("system/%s/state" % config['mqtt']['name'], payload='offline', qos=2, retain=True)
mqttc.connect(config['mqtt']['server'], 1883, 60)
mqttc.publish("system/%s/state" % config['mqtt']['name'], payload='online', qos=2, retain=True)
mqttc.publish("door/%s/rebooted" % config['door']['name'])
mqttc.loop_start()

ser.write(b'E')


def report_activity(card_id):
    try:
        url = 'https://members.hacman.org.uk/acs/activity'
        data = {
            'tagId': card_id,
            'device': config['member_system']['device']
        }
        headers = {
            'ApiKey': config['member_system']['api_key']
        }
        requests.post(url, data=json.dumps(data), headers=headers)
    except:
        logging.error("Error reporting activity for ID %s", card_id)


while True:
    card_id = ser.readline().decode("utf-8").strip()

    if card_id:
        logging.debug(card_id)

        if card_id == 'D0-0':
            logging.info('Door Button Pressed')
            mqttc.publish("door/%s/opened/button" %
                          config['door']['name'], qos=2)
            ser.write(b'1')

        if (card_id[0] == 'C'):
            card_id = card_id[1:]
            if card_id[0:2] == '88':
                card_id = card_id[2:]

            logging.info("Card ID: %s", card_id)
            found = False

            with open('members', 'r') as members_f:
                for member in members_f.readlines():
                    member = member.strip().split(',')
                    if member[0].lower().startswith(card_id):
                        ser.write(b'1')
                        ser.write(b'G')
                        found = True
                        logging.info(
                            "%s found, %s opened the door!", card_id, member[1])
                        mqttc.publish("door/%s/opened/username" %
                                      config['door']['name'], member[1], qos=2)
                        report_activity(card_id)

            if not found:
                ser.write(b'R')
                logging.info("%s not found!", card_id)
                mqttc.publish("door/%s/invalidcard" %
                              config['door']['name'], qos=2)
