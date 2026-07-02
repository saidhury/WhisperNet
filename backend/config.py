import os

PROTOCOL_VERSION = 1
# Allow overriding the nickname via an Environment Variable
NICKNAME = os.getenv("NICKNAME", "DefaultUser")