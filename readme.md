# RounefordBot <img align="right" src="https://raw.githubusercontent.com/Ar4ikov/Rouneford/master/images/Rouneford_icon.png" height="170" width="170">

А зачем? А нафига? Да просто так!

Коротко о боте:
---
- Открытость и свободно редактируемый код, понятный и удобный для разработки
- Поддержка сторонних плагинов
- Реализация на официальном API - discord.py (https://discordpy.readthedocs.io)
- Простота в настройке и дополнении
- Удобный функционал засчёт добавления кастомных функций
- Стартовые плагины для полноценной функциональности бота на сервере, включая стриминг аудио

## 1. Установка

- ####Установка на устройство

Установка производится путём клонирования репозитория на ваше устройство
```console
root@Ar4kov:~$ git clone https://github.com/Ar4ikov/Rouneford/ Rounedford
```

- ####Установка дополнений

Для работы бота необходимо иметь в наличии библиотеки: `discord.py`, `youtube-dl`, `ffmpeg` и `asyncio` (Стандартную, если таковой не
имелось изначально)

```console
root@Ar4ikov:~$ pip install discord.py[voice]
root@Ar4ikov:~$ pip install youtube-dl
root@Ar4ikov:~$ pip install asyncio
root@Ar4ikov:~$ pip install ffmpeg
```

## 2. Настройка и запуск бота

- #### Получение токена бота

Больше информации о получении Access-token бота вы можете получить [`тут`](https://github.com/reactiflux/discord-irc/wiki/Creating-a-discord-bot-%26-getting-a-token)

- #### Настройка `bot.py`

```python
from core.core import RounefordBot

bot = RounefordBot(access_token="Ваш-Bot-Token")
bot.run()

```

## 3. Создание собственных плагинов

### Список стандартных плагинов будет пополняться.

- #### Создание директории

Необходимо создать директорию плагина в папке `plugins`, которая должна выглядеть следующим образом:
```console
├── __init__.py
├── plugin.py
└── немного файлов здесь
```

В файле `__init__.py` необходимо импортировать ваш основной класс плагина
```python
from plugins.TestPlugin.test_plugin import Plugin
```

- #### Инициализация класса


Класс может иметь абсолютно любое название, однако должен содержать следующие свойства ниже и быть унаследован от класса
`core.api.BotPlugin`

```python
from core.api import BotPlugin
from discord.ext.commands import Bot as Client

class Plugin(BotPlugin):
    def __init__(self, client: Client):
        super().__init__(client)

        self.plugin_name = "Test Plugin"               # Имя плагина
        self.author = "https://github.com/Ar4ikov/"    # Автор
        self.version = "1.0.1"                         # Версия
        self.plugin_id = "test_plugin"                 # Id плагина
        self.description = """Simple plugin"""         # Описание
        self.tasks = ["task_1"]                        # Имена фоновых задач
        self.commands = {}                             # Описание команд плагина вида {"command": "how works"}
```

- #### Определение фоновых задач

```python
from asyncio import sleep

async def background_task_1(self):
        """Имя фоновой задачи выглядит следующим образом:
        - background_{name}
        где: 
          - {name} - Имя задачи из `self.tasks`"""
          
        while True:
            await sleep(1)
            print(self.plugin_name, "Готов к труду и обороне!")

```

- #### Определение команд

```python
async def cmd_kek(self, channel, member, *args, **kwargs):
        await self.send_message(channel, "Вас только что 'кекнули'!")
```

- #### Логирование
```python
from core.objects import Logger
logger = Logger("my_logs")
logger.log("info")

# Клиент содержит в себе экзлемпляр класса Logger, но вы можете создать свой логгер (как это сделано выше)
self.client.logging.log("Запущен новый процесс")
self.client.logging.log("{} >> [}".format(member.name, " ".join(args)))
```

- #### Запуск плагина

```python
from discord import Member  # Не несёт смысловой нагрузки, исключительно в косметических целях

async def run(self):
    super().run()
    @self.client.listen()
    async def on_member_join(member: Member):
        print(member.name, "зашёл на сервер!")
```
