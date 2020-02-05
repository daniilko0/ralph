from enum import Enum


class States(Enum):
    MAIN = "main"
    CALL_MESSAGE_ASK = "call_message_ask"
    CALL_CONFIG = "call_config"
    MAILING_MESSAGE_ASK = "mailing_message_ask"
    MAILING_CONFIRM = "mailing_confirm"
    SCHEDULE_DATE_ASK = "schedule_date_ask"
