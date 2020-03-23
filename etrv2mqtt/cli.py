#!/usr/bin/env python3

import sys
from libetrv.bluetooth import btle
from libetrv.device import eTRVDevice
from loguru import logger

from etrv2mqtt.etrvutils import eTRVUtils
from etrv2mqtt.config import Config
from etrv2mqtt.mqtt import Mqtt

import time
from typing import Dict

mqtt:Mqtt

def poll_device(devices: Dict[str, eTRVDevice], name:str):
    try:
        device=devices[name]
        logger.debug("Polling data from {}", name)
        ret = eTRVUtils.read_device(device)
        logger.debug(str(ret))
        mqtt.publish_device_data(name, str(ret))
    except btle.BTLEDisconnectError as e:
        logger.error(e)

def poll_devices(devices: Dict[str, eTRVDevice]):
    for name in devices.keys():
        poll_device(devices, name)

def set_temperature_callback(devices: Dict[str, eTRVDevice], name: str, temperature: float):
    if name not in devices.keys():
        logger.warning(
            "Attempting to set temperature for non existing device {}", name)
        return
    try:
        logger.debug("Setting {} to {}C", name, temperature)
        device = devices[name]
        eTRVUtils.set_temperature(device, temperature)
        # Home assistant needs to see updated temperature value to confirm change
        poll_device(devices, name)
    except btle.BTLEDisconnectError as e:
        logger.error(e)


def main(config_file: str):

    try:
        config = Config(config_file)
    except Exception as e:
        logger.error(e)
        sys.exit(1)

    devices:Dict[str, eTRVDevice] = {}

    for thermostat_config in config.thermostats.values():
        logger.debug("Adding {} MAC: {} key: {}", thermostat_config.topic, thermostat_config.address, thermostat_config.secret_key)
        device = eTRVUtils.create_device(thermostat_config.address, bytes.fromhex(thermostat_config.secret_key), retry_limit=config.retry_limit)
        devices[thermostat_config.topic] = device
    
    global mqtt
    mqtt = Mqtt(config, devices, set_temperature_callback)

    while True:
        poll_devices(devices)
        time.sleep(config.poll_interval)

def usage():
    print('Usage: '+sys.argv[0]+' configfile.json')
    sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) <2:
        usage()
    else:
        main(sys.argv[1])
    
