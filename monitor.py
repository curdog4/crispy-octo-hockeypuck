#!/usr/bin/env python

from __future__ import print_function
import os, sys
import picamera
import time
import datetime
import random
import httplib2

from googleapiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from googleapiclient.http import MediaFileUpload

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Raspberry Pi Camera Monitor'

def get_credentials():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'pimonitor.json')
    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def main():
    # sleep for 0 - 10 minutes
    time.sleep(600.0 * random.random())
    #camera = picamera.PiCamera(resolution=(720,480), framerate=Fraction(1, 6), sensor_mode=3)
    camera = picamera.PiCamera(resolution=(720, 480))
    camera.led = False
    #
    # allow 5 seconds for the camera to adjust
    #
    time.sleep(5.0)
    #
    # now fix properties for lighting
    #

    ##
    # Day mode shot...
    camera.iso = 600
    camera.shutter_speed = camera.exposure_speed
    camera.exposure_mode = "off"
    gains = camera.awb_gains
    camera.awb_mode = "off"
    camera.awb_gains = gains

    ##
    # Night mode shot...
    #camera.shutter_speed = 10000000
    #camera.iso = 800
    #time.sleep(30.0)
    #camera.exposure_mode = "off"

    timestamp = datetime.datetime.now().isoformat()
    camera.capture('{0:s}.jpeg'.format(timestamp))
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)
    file_meta = {'name': '{0:s}.jpeg'.format(timestamp),
                 'parents': ['0Bylh67N_jGJoR3pkR1FKVGdscXM']}
    media = MediaFileUpload('{0:s}.jpeg'.format(timestamp),
                            mimetype='image/jpeg')
    #result = service.files().list(
    #    pageSize=20, fields="nextPageToken, files(id, name)").execute()
    #items = result.get('files', [])
    #if not items:
    #    print("Not files found.")
    #else:
    #    print("Files:")
    #    for item in items:
    #        print("{0} ({1})".format(item['name'], item['id']))
    result = service.files().create(body=file_meta,
                                     media_body=media,
                                     fields='id').execute()
    os.unlink('{0:s}.jpeg'.format(timestamp))
    sys.exit(0)

if __name__ == "__main__":
    main()
