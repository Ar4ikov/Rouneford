# | Created by Ar4ikov
# | Время: 12.02.2019 - 14:20
from asyncio import sleep

from core.core import RounefordBot as Client

from core.api import BotPlugin
from core.objects import BotEmbed


class Plugin(BotPlugin):
    def __init__(self, client: Client):
        super().__init__(client)

        self.plugin_name = "Test Plugin"
        self.author = "https://github.com/Ar4ikov/"
        self.version = "1.0.1"
        self.plugin_id = "test_plugin"
        self.description = """Simple plugin"""
        self.tasks = []

    async def cmd_kek(self, channel, member, *args, **kwargs):
        await self.send_message(channel, embed=BotEmbed().set_settings(
            name="тестовый эмбед",
            desc="Это описание",
        ), delete_after=5)

    async def background_task_1(self):
        while True:
            await sleep(1)
            print(self.plugin_name, "Готов к труду и обороне!")

    async def background_task_2(self):
        while True:
            await sleep(1)
            print(self.plugin_name, "пришёл в готовность!")

    async def empty_event(self):
        pass

    async def run(self):
        pass
