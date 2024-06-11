import os

class BaseConfig():
    SECRET_KEY = "Socialist Republic of Ligmaballz"
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.abspath(os.curdir)}/john_xina.db'
    WTF_CSRF_ENABLED = False    # because it just so hard to deal with...

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    ENV = 'development'

class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

class ProductionConfig(BaseConfig):
    DEBUG = False
    TESTING = False

# create a function that will just return a specified configuration
# for some reason, python acts like the config class doesn't exists, so I created this function as a workaround
def getConfig(name):
    if name == 'DEV':
        return DevelopmentConfig
    elif name == 'TEST':
        return TestingConfig
    elif name == 'PROD':
        return ProductionConfig
    else:
        raise ImportError('Config does not exists')