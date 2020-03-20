from importlib import resources as importlib_resources
import json
from jsonschema import validate
from dataclasses import dataclass


@dataclass
class _ThermostatConfig:
    topic: str
    address: str
    secret_key: str


@dataclass
class _MQTTConfig:
    server: str
    port: int
    base_topic: str
    user: str = None
    password: str = None


class Config:
    def __init__(self, filename: str):
        _config_schema = json.load(importlib_resources.open_text(
            'etrv2mqtt.schemas', 'config.schema.json'))

        with open(filename, 'r') as configfile:
            _config_json = json.load(configfile)
            validate(instance=_config_json, schema=_config_schema)

        self.mqtt = _MQTTConfig(
            _config_json['mqtt']['server'],
            _config_json['mqtt']['port'],
            _config_json['mqtt']['base_topic'],
            _config_json['mqtt']['user'] if 'user' in _config_json['mqtt'].keys() else None,
            _config_json['mqtt']['password'] if 'password' in _config_json['mqtt'].keys() else None
        )
        self.retry_limit = _config_json['retry_limit']
        self.poll_interval = _config_json['poll_interval']
        self.thermostats = {}
        for t in _config_json['thermostats']:
            self.thermostats[t['topic']] = _ThermostatConfig(
                t['topic'],
                t['address'],
                t['secret_key']
            )
