# | Created by Ar4ikov
# | Время: 04.02.2019 - 20:16
import discord
from discord import Message
from discord.ext.commands import Bot as Client
import asyncio

from core.module import Modules
from core.objects import BotEmbed, BotEnums, BotColors, Logger


class RounefordBot(Client):

    def __init__(self, access_token=None, bot_tag="//"):
        super().__init__(command_prefix=bot_tag)

        if not access_token:
            raise ValueError("Вы не указали Access-token вашего бота.")

        self.access_token = access_token
        self.bot_tag = bot_tag

        self.logging = Logger("logs")

        self.modules = Modules()
        self.plugins = []

    async def empty_task(self):
        """Пустая задача для возврата неопределённых фоновых задач при запуске плагинов"""
        pass

    async def cmd_help(self, channel: discord.Channel, member: discord.Member, args):
        await self.wait_until_ready()

        if args:
            plugin_name = [x for x in self.plugins if x.plugin_id == args[0]]
            if not plugin_name:
                await self.send_message(channel, embed=BotEmbed().set_settings(
                    name="Не найден указанный плагин :(",
                    color=BotColors.RED.value
                ))

                return True

            helping = {}

            for command, desc in plugin_name[0].commands.items():
                helping["`{}`".format(self.bot_tag + command)] = "*{}*".format(desc)

            await self.send_message(channel, embed=BotEmbed().set_settings(
                name="Помощь по командам плагина `{}`".format(plugin_name[0].plugin_name),
                desc="//help - помощь по командам бота",
                fields=helping,
                author_icon="https://raw.githubusercontent.com/Ar4ikov/Rouneford/master/images/Rouneford_icon.png",
                author_name="Rouneford Discord Bot",
                footer="powered by https://github.com/Ar4ikov/Rouneford",
                color=0x46b3ff
            ))

            return True

        helping = {"Основные команды": " ".join(
            ["`{}`".format(self.bot_tag + x.replace("cmd_", "")) for x in dir(self) if x.startswith("cmd_")])}

        for plugin in self.plugins:
            cmds = ["`{}`".format(self.bot_tag + x) for x in plugin.commands.keys()]

            helping[plugin.plugin_name + " -> {}".format(plugin.plugin_id)] = " ".join(
                cmds) or "Плагин не имеет встроенных команд :("

        await self.send_message(channel, embed=BotEmbed().set_settings(
            name="Помощь по командам",
            desc="//help - помощь по командам бота",
            fields=helping,
            author_icon="https://raw.githubusercontent.com/Ar4ikov/Rouneford/master/images/Rouneford_icon.png",
            author_name="Rouneford Discord Bot",
            footer="powered by https://github.com/Ar4ikov/Rouneford",
            color=0x46b3ff
        ))

        return True

    async def cmd_about(self, channel: discord.Channel, member: discord.Member, args):
        await self.wait_until_ready()
        await self.send_message(channel, embed=BotEmbed().set_settings(
            name="Здесь должно было быть описание бота, но мне лень его делать.",
            desc="`Автор`: **https://github.com/Ar4ikov**\n`GitHub`: **https://github.com/Ar4ikov/Rouneford**\n",
            author_icon="https://raw.githubusercontent.com/Ar4ikov/Rouneford/master/images/Rouneford_icon.png",
            author_name="Rouneford Discord Bot"
        ))

        return True

    async def cmd_plugins(self, channel: discord.Channel, member: discord.Member, args):
        await self.wait_until_ready()

        plugs = {}
        for plugin_ in self.plugins:
            plugs["`{}`".format(plugin_.plugin_name)] = """Автор: `{}`\nВерсия: `{}`\n*{}*\n ~~-----------~~ """.format(
                plugin_.author, plugin_.version, plugin_.description
            )

        await self.send_message(channel, embed=BotEmbed().set_settings(
            name="Плагины Бота:",
            desc="//plugins - Информация о загруженных плагинах в бота",
            fields=plugs,
            footer="powered by https://github.com/Ar4ikov/RouinefordBot",
            color=0x46b3ff
        ))

        return True

    def run(self, *args, **kwargs):

        params = {}

        """Запуск валидных плагинов и их фоновых задач"""

        for module in self.modules.get_modules()[0]:
            self.plugins.append(module.get("plugin")(self, **params))

        """Сортировка по приоритету"""
        self.plugins = sorted(self.plugins, key=lambda x: x.priority.value, reverse=True)

        for plugin in self.plugins:
            for task in plugin.tasks:
                self.loop.create_task(getattr(plugin, BotEnums.TASK_FUNC_PREFIX.value.format(task), self.empty_task)())

            # Запуск основной функции плагина
            self.loop.create_task(plugin.run())

        """Игра с эвентами"""

        @self.listen()
        async def on_ready():
            print("Rouneford готов к эксплуатации!")

        @self.event
        async def on_message(message: Message):

            log_ = "[${}] [#{}] @{}: {}".format(getattr(message.server, "name", None) or "No-server",
                                                getattr(message.channel, "name", None) or "Private",
                                                message.author.name,
                                                message.content)

            self.logging.log(self, log_)

            message_ = message.content.split(" ")
            cmd = message_[0]

            if cmd.count(self.bot_tag):

                call_ = getattr(self, BotEnums.CMD_FUNC_PREFIX.value.format(cmd.lower()[len(self.bot_tag):]), None)

                if call_:
                    await call_(message.channel, message.author, message_[1:])
                else:
                    for plugin_ in self.plugins:
                        func = getattr(plugin_, BotEnums.CMD_FUNC_PREFIX.value.format(cmd.lower()[len(self.bot_tag):]),
                                       None)

                        if func:
                            await func(message.channel, message.author, *message_[1:])
                            break

        super().run(self.access_token, *args, **kwargs)
