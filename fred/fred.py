#!/usr/bin/python
import serial
import pygame
import sys
import logging
import socket
import re
import mosquitto

door_name = "inner"

mqttc = mosquitto.Mosquitto("alfred_%sdoor" % door_name)
mqttc.connect("alfred", 1883, 60, True)

ser = serial.Serial("/dev/alfie", 9600)

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

logging.info("FRED 0.4")

mqttc.publish("door/%s/rebooted" % door_name)

while 1:
    mqttc.loop()
    card_id = ser.readline().strip()

    if card_id == 'B':
        if not pygame.mixer.music.get_busy():
            pygame.mixer.music.play()
            logging.info('Buzzer')
            mqttc.publish("door/%s/buzzer" % door_name)
    elif card_id == 'O':
        logging.info('Door Button Pressed')
        mqttc.publish("door/%s/opened/button" % door_name)
        ser.write('1')
    elif card_id == 'D':
        if not pygame.mixer.music.get_busy():
            pygame.mixer.music.play()
            logging.info('Doorbell')
            mqttc.publish("door/%s/doorbell" % door_name)
    elif card_id[0] == 'C':
	card_id = card_id[1:]
	if card_id[0:1]:
		card_id = card_id[2:]
        logging.info("Card ID: %s", card_id)
        found = False

        members_f = open('members', 'r')
        members = members_f.readlines()

        for member in members:
            member = member.strip().split(',')
            if card_id in member[0]:
                ser.write('1')
                ser.write('G')
                found = True
                logging.info("%s found, %s opened the door!", card_id, member[1])
                mqttc.publish("door/%s/opened/username" % door_name, member[1])
        if not found:
            ser.write('R')
            logging.info("%s not found!", card_id)
            mqttc.publish("door/%s/invalidcard" % door_name)
        members_f.close()
