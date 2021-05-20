import pymysql

class Config:
    SECRET_KEY = 'ab62f053dc6f3bd97654d729bb670fad'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://admin:admin123@127.0.0.1/portal3'
    SQLALCHEMY_TRACK_MODIFICATIONS = False