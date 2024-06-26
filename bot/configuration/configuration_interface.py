class ConfigurationInterface():
    def get(self, injectable):
        raise NotImplementedError("Configuration accessor not defined")