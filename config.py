import yaml

class Config(object):
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self):
        with open(self.config_file, 'r') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        return config

    def get(self, key):
        return self.config.get(key)

    def get_all(self):
        return self.config
