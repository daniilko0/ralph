from vk_api.bot_longpoll import VkBotLongPoll


class RalphVkBotLongPoll(VkBotLongPoll):
    def listen(self):
        while True:
            try:
                for event in self.check():
                    yield event
            except Exception as err:
                print(f"Error: {err}.")
