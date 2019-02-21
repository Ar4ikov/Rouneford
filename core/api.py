# | Created by Ar4ikov
# | Время: 12.02.2019 - 13:02

from abc import abstractmethod
from enum import Enum
from discord import Message
from asyncio import sleep

from core.objects import BotEmbed, BotEnums
from discord.ext.commands import Bot as Client


class BotEvents(Enum):
    """
    Эвенты, которые поддерживает discord.py

    Эвент ON_MESSAGE нежелательно импортировать или поддерживать в своём проекте.

    """
    ON_READY = "on_ready"
    ON_RESUMED = "on_resumed"
    ON_ERROR = "on_error"

    ON_MESSAGE = "on_message"
    ON_SOCKET_RAW_RECEIVE = "on_socket_raw_receive"
    ON_SOCKET_RAW_SEND = "on_socket_raw_send"
    ON_MESSAGE_DELETE = "on_message_delete"
    ON_MESSAGE_EDIT = "on_message_edit"

    ON_REACTION_ADD = "on_reaction_add"
    ON_REACTION_REMOVE = "on_reaction_remove"
    ON_REACTION_CLEAR = "on_reaction_clear"

    ON_CHANNEL_DELETE = "on_channel_delete"
    ON_CHANNEL_UPDATE = "on_channel_update"
    ON_CHANNEL_CREATE = "on_channel_create"

    ON_MEMBER_JOIN = "on_member_join"
    ON_MEMBER_REMOVE = "on_member_remove"
    ON_MEMBER_UPDATE = "on_member_update"

    ON_SERVER_JOIN = "on_server_join"
    ON_SERVER_REMOVE = "on_server_remove"
    ON_SERVER_UPDATE = "on_server_update"

    ON_SERVER_ROLE_CREATE = "on_server_role_create"
    ON_SERVER_ROLE_DELETE = "on_server_role_delete"
    ON_SERVER_ROLE_UPDATE = "on_server_role_update"

    ON_SERVER_EMOJIS_UPDATE = "on_server_emojis_update"

    ON_SERVER_AVAILABLE = "on_server_available"
    ON_SERVER_UNAVAILABLE = "on_server_unavailable"

    ON_VOICE_STATE_UPDATE = "on_voice_state_update"

    ON_MEMBER_BAN = "on_member_ban"
    ON_MEMBER_UNBAN = "on_member_unban"

    ON_TYPING = "on_typing"

    ON_GROUP_JOIN = "on_group_join"
    ON_GROUP_REMOVE = "on_group_remove"


class Priority(Enum):
    LOW_PRIORITY = 0
    MEDIUM_PRIORITY = 1
    HIGH_PRIORITY = 2
    HIGHEST = 3
    CORE_PLUGIN = 4


class BotPlugin:
    """
    Сия класс молодым и начинающим кодерам придётся импортировать как основной класс их собственного плагина для данного
    бота.

    [-] Существует поддержка фоновых задач, их имена стоит указать в `self.tasks`
    [-] Ддя начала работы с эвентами стоит объявить их в методе `run()`, предварительно,
    вывзав его из родительского класса -> super().run()
    [-] Прочие параметры, указанные в конструкторе, обязательны к заполнению.

    Если ваш плагин будет иметь внутренние команды, следует создать метод `cmd_{}`, где вместо {} используйте
    латинское отображение вашей команды. Ядро бота само определит, где будет находиться ваша команда.
    Старайтесь не создавать одинаковые по названию команды. Если же ваш плагин должен быть основным, следует задать прио
    ритет вашему плагину. указав его в конструкторе, как Priority.HIGHEST

    """

    @abstractmethod
    def __init__(self, client: Client, **kwargs):
        self.plugin_root = "root"  # НЕ ТРОГАЙ ЭТО!
        self.tasks = []
        self.plugin_name = None
        self.author = "Author"
        self.version = "1.0.0"
        self.plugin_id = None
        self.description = """This is description about workable of my own plugin for discord bot"""

        self.client = client
        self.priority = Priority.LOW_PRIORITY

        self.bot = kwargs.get("bot")
        self.server_id = kwargs.get("server_id")

        self.commands = {}

    async def send_message(self, channel, content=None, embed=None, delete_after=0) -> Message:
        """
        Удобный метод отправки сообщения.
        :param channel: Канал
        :param content: Текст сообщения
        :param embed: Объект сообщения
        :param delete_after: Таймаут удаления сообщения
        :return: discord.Message
        """

        if type(content) == str and type(embed) == BotEmbed:
            message_ = await self.client.send_message(channel, content, embed=embed)
        elif type(embed) == BotEmbed and not content:
            message_ = await self.client.send_message(channel, embed=embed)
        elif type(content) == str and not embed:
            message_ = await self.client.send_message(channel, content)
        else:
            raise ValueError(BotEnums.CANNOT_SEND_EMPTY_MESSAGE)

        if delete_after:
            async def msg_timeout(timeout, message):
                await sleep(timeout)
                await self.client.delete_message(message)

            self.client.loop.create_task(msg_timeout(delete_after, message_))

        return message_

    def __eq__(self, other):
        return getattr(other, "priority", Priority.LOW_PRIORITY) == self.priority

    def __ne__(self, other):
        return getattr(other, "priority", Priority.LOW_PRIORITY) != self.priority

    def __lt__(self, other):
        return getattr(other, "priority", Priority.LOW_PRIORITY.value) < self.priority.value

    def __gt__(self, other):
        return getattr(other, "priority", Priority.LOW_PRIORITY.value) > self.priority.value

    def __le__(self, other):
        return getattr(other, "priority", Priority.LOW_PRIORITY.value) <= self.priority.value

    def __ge__(self, other):
        return getattr(other, "priority", Priority.LOW_PRIORITY.value) >= self.priority.value

    def __str__(self):
        return self.plugin_id

    def __int__(self):
        return self.priority.value

    @abstractmethod
    async def run(self):
        """Тезнические переменные и корретировки при загрузке плагина ядром бота"""
        await self.client.wait_until_ready()

        if not self.bot:
            self.bot = await self.client.application_info()
        else:
            self.bot = await self.bot
