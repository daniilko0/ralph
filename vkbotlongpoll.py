# Эта хрень нужна, чтобы бот не останавливался каждый день примерно в три часа ночи (ВК перезапускает свои сервера)
# Подробнее здесь: https://github.com/python273/vk_api/issues/144#issuecomment-404023710

from vk_api.bot_longpoll import VkBotLongPoll

class RalphVkBotLongPoll(VkBotLongPoll):
    def listen(self):
        while True:
            try:
                for event in self.check():
                    yield event
            except Exception as err:
                print(f"Error: {err}.")
