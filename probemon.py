#!/usr/bin/python

import time
import datetime
import argparse
import netaddr
import sys
import logging

import requests
import json

from scapy.all import *
from pprint import pprint
from logging.handlers import RotatingFileHandler

defaultencoding = 'utf-8'
if sys.getdefaultencoding() != defaultencoding:
        reload(sys)
        sys.setdefaultencoding(defaultencoding)

NAME = 'probemon'
DESCRIPTION = "a command line tool for logging 802.11 probe request frames"

DEBUG = False

def build_packet_callback(time_fmt, logger, delimiter, mac_info, ssid, rssi):
	def packet_callback(packet):
		
		if not packet.haslayer(Dot11):
			return

		# we are looking for management frames with a probe subtype
		# if neither match we are done here
		if packet.type != 0 or packet.subtype != 0x04:
			return
                
                if packet.info == 'dlink-RTESLab' or packet.addr2 == '7c:dd:90:e4:ed:2f':
                        return

		# list of output fields
		fields = []

		# determine preferred time format 
		log_time = str(int(time.time()))
		if time_fmt == 'iso':
			log_time = datetime.now().isoformat()

		fields.append(log_time)

		# append the mac address itself
		fields.append(packet.addr2)

		# parse mac address and look up the organization from the vendor octets
		if mac_info:
			try:
				parsed_mac = netaddr.EUI(packet.addr2)
				fields.append(parsed_mac.oui.registration().org)
			except netaddr.core.NotRegisteredError, e:
				fields.append('UNKNOWN')

		# include the SSID in the probe frame
		if ssid:
			fields.append(packet.info)
			
		if rssi:
			rssi_val = -(256-ord(packet.notdecoded[-2:-1]))
			fields.append(str(rssi_val))

		logger.info(delimiter.join(fields))

	return packet_callback

def main():
	parser = argparse.ArgumentParser(description=DESCRIPTION)
	parser.add_argument('-i', '--interface', help="capture interface")
	parser.add_argument('-t', '--time', default='iso', help="output time format (unix, iso)")
	parser.add_argument('-o', '--output', default='probemon.log', help="logging output location")
	parser.add_argument('-b', '--max-bytes', default=5000000, help="maximum log size in bytes before rotating")
	parser.add_argument('-c', '--max-backups', default=99999, help="maximum number of log files to keep")
	parser.add_argument('-d', '--delimiter', default='\t', help="output field delimiter")
	parser.add_argument('-f', '--mac-info', action='store_true', help="include MAC address manufacturer")
	parser.add_argument('-s', '--ssid', action='store_true', help="include probe SSID in output")
	parser.add_argument('-r', '--rssi', action='store_true', help="include rssi in output")
	parser.add_argument('-D', '--debug', action='store_true', help="enable debug output")
	parser.add_argument('-l', '--log', action='store_true', help="enable scrolling live view of the logfile")
	args = parser.parse_args()

	if not args.interface:
		print "error: capture interface not given, try --help"
		sys.exit(-1)
	
	DEBUG = args.debug
        
        #msg = {"type": "note", "title": "RPi_102", "body": "Sniffer On"}
        #TOKEN = 'o.nm5hrJ6RbTTpOVPlkgal1k0ByraB8DuI'
        #resp = requests.post('https://api.pushbullet.com/v2/pushes', data=json.dumps(msg),
        #                headers={'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json'})
        #if resp.status_code != 200:
        #        raise Exception('Something wrong')
        #else:
        #        print 'complete sending'

	# setup our rotating logger
	logname = datetime.now().strftime('%Y%m%d')+'.log'
        logger = logging.getLogger(NAME)
	logger.setLevel(logging.INFO)
	handler = RotatingFileHandler(logname, maxBytes=args.max_bytes, backupCount=args.max_backups)
	logger.addHandler(handler)
	if args.log:
		logger.addHandler(logging.StreamHandler(sys.stdout))
	built_packet_cb = build_packet_callback(args.time, logger, 
		args.delimiter, args.mac_info, args.ssid, args.rssi)
	sniff(iface=args.interface, prn=built_packet_cb, store=0)

if __name__ == '__main__':
	main()
