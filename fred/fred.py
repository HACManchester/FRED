#!/usr/bin/python
import serial
import sys
import logging
import socket
import re
import mosquitto
import yaml

config_f = open('config.yaml')
config = yaml.safe_load(config_f)
config_f.close()

mqttc = mosquitto.Mosquitto(config['door']['mqtt_name'])
mqttc.connect("acidburn", 1883, 60, True)

ser = serial.Serial(config['serial']['port'], config['serial']['baud'], timeout=0.5)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s %(message)s')

fh = logging.FileHandler('fred.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)

logger.addHandler(ch)

logging.info("FRED 0.7")

mqttc.publish("door/%s/rebooted" % config['door']['name'])
mqttc.loop_start()

ser.write('E')

while 1:
    card_id = ser.readline().strip()

    if card_id:
        logging.debug(card_id)

    if not card_id:
	pass
    elif card_id == 'D0-0':
        logging.info('Door Button Pressed')
        mqttc.publish("door/%s/opened/button" % config['door']['name'], qos=2)
        ser.write('1')
    elif card_id[0:3] == 'A1-' and int(card_id[3:7]) < 100:
        logging.info('Doorbell pressed')
        mqttc.publish("door/%s/doorbell" % config['door']['name'], qos=1)
    elif (config['hardware']['version'] == 'old' and card_id != '00000000000000') or (card_id[0] == 'C'):
	if config['hardware']['version'] == 'new':
		card_id = card_id[1:]
        	if card_id[0:2] == '88':
                	card_id = card_id[2:]

        logging.info("Card ID: %s", card_id)
        found = False

        members_f = open('members', 'r')
        members = members_f.readlines()

        for member in members:
            member = member.strip().split(',')
            if member[0].startswith(card_id):
                ser.write('1')
                ser.write('G')
                found = True
                logging.info("%s found, %s opened the door!", card_id, member[1])
                mqttc.publish("door/%s/opened/username" % config['door']['name'], member[1], qos=2)
        if not found:
            ser.write('R')
            logging.info("%s not found!", card_id)
            mqttc.publish("door/%s/invalidcard" % config['door']['name'], qos=2)
        members_f.close()
    elif (card_id[0] == 'A'):
	mqttc.publish("sensor/door/%s/analog/%s" % (config['door']['name'], card_id[1]), card_id.split('-')[1], qos=2)
    elif (card_id[0] == 'D'):
        mqttc.publish("sensor/door/%s/digital/%s" % (config['door']['name'], card_id[1]), card_id.split('-')[1], qos=2)

