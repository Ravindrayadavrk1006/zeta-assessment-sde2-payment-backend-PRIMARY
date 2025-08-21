import json
import os

#the config.json is ignored, refer to config_sample.json and provide the secrets in that file and rename it to config.json before starting the server
with open('config.json', "r") as f:
    config = json.load(f)