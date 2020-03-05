# Эта хрень нужна, чтобы бот не останавливался каждый день примерно в три часа ночи (ВК перезапускает свои сервера)
# Подробнее здесь: https://github.com/python273/vk_api/issues/144#issuecomment-404023710

from vk_api.bot_longpoll import VkBotLongPoll
from logger import init_logger


class RalphVkBotLongPoll(VkBotLongPoll):
    def __init__(self, vk, group_id, wait=25):
        super().__init__(vk, group_id, wait)
        self.log = init_logger()

    def listen(self):
        while True:
            try:
                for event in self.check():
                    yield event
            except Exception as err:
                self.log.info(f"Error: {err}.")
