#!/usr/bin/python
import serial
import pygame
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
mqttc.connect("alfred", 1883, 60, True)

ser = serial.Serial(config['serial']['port'], config['serial']['baud'], timeout=0.5)

pygame.mixer.init(44100, -16, 2, 2048)
pygame.mixer.music.set_volume(1)
pygame.mixer.music.load("doorbell.ogg")

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

logging.info("FRED 0.5")

mqttc.publish("door/%s/rebooted" % config['door']['name'])

while 1:
    mqttc.loop()
    card_id = ser.readline().strip()

    if not card_id:
	pass
    elif card_id == 'B':
        if not pygame.mixer.music.get_busy():
            pygame.mixer.music.play()
            logging.info('Buzzer')
            mqttc.publish("door/%s/buzzer" % config['door']['name'])
    elif card_id == 'O':
        logging.info('Door Button Pressed')
        mqttc.publish("door/%s/opened/button" % config['door']['name'])
        ser.write('1')
    elif card_id == 'D':
        if not pygame.mixer.music.get_busy():
            pygame.mixer.music.play()
            logging.info('Doorbell')
            mqttc.publish("door/%s/doorbell" % config['door']['name'])
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
                mqttc.publish("door/%s/opened/username" % config['door']['name'], member[1])
        if not found:
            ser.write('R')
            logging.info("%s not found!", card_id)
            mqttc.publish("door/%s/invalidcard" % config['door']['name'])
        members_f.close()
    elif (card_id[0] == 'A'):
	mqttc.publish("sensor/door/%s/analog/%s" % (config['door']['name'], card_id[1]), card_id.split('-')[1])
    elif (card_id[0] == 'D'):
        mqttc.publish("sensor/door/%s/digital/%s" % (config['door']['name'], card_id[1]), card_id.split('-')[1])

