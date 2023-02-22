from enum import Enum

class Constants:
    class Status(Enum):
        ACTIVE = 1
        INACTIVE = 0
        DELETED = -1
    class PhoneNumberTypes(Enum):
        SELF = 'Self'
        INTERNAL = 'Internal'
        EXTERNAL = 'External'