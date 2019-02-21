# | Created by Ar4ikov
# | Время: 12.02.2019 - 12:53
import datetime
import os
from enum import Enum
from discord import Embed


class BotColors(Enum):
    RED = 0xff0000
    BLUE = 0x0000ff
    GREEN = 0x008000
    WHITE = 0xffffff
    BLACK = 0x000000

    """Немного больце цветов появятся позже"""


class Logger:
    class LogLevel(Enum):
        INFO = 1
        WARNINGS = 2

    def __init__(self, log_dir):
        self.log_dir = log_dir

        if not os.path.isdir(self.log_dir):
            os.mkdir(self.log_dir)

    def log(self, cls, log_content):
        print(log_content)
        dt = datetime.datetime.today()
        with open(self.log_dir + "/{}_{}_{}.txt".format(dt.year, dt.month, dt.day), "a+") as log_file:
            log_file.write("{} | [{}] | {}\n".format(
                dt.strftime("%Y-%m-%d %H:%M:%S"),
                getattr(cls, "plugin_name", "SYSTEM"),
                log_content
            ))

        return log_content


class BotEmbed(Embed):
    def __init__(self):
        super().__init__()

    def set_settings(self, name, url=None, desc=None, color=0xffffff, fields: dict = None, author_name=None,
                     author_icon=None,
                     thumbnail=None, footer=None):
        if fields:
            for key, value in fields.items():
                self.add_field(name=key, value=value, inline=False)

        if thumbnail:
            self.set_thumbnail(url=thumbnail)

        if footer:
            self.set_footer(text=footer)

        if author_name and author_icon:
            self.set_author(name=author_name, icon_url=author_icon)

        self.title = name
        self.description = desc
        self.color = color
        self.url = url

        return self


class BotEnums(Enum):
    CANNOT_SEND_EMPTY_MESSAGE = "Вы не можете отправить пустое сообщение"

    USER = "пользователь"
    MEMBER = "участник"
    MEMBER_MENTION = "<@!{}>"
    ROLE_MENTION = "<@&{}>"
    BOT = "бот"
    SERVER = "сервер"
    PLUGIN = "плагин"

    CMD_FUNC_PREFIX = "cmd_{}"
    TASK_FUNC_PREFIX = "background_{}"
