# | Created by Ar4ikov
# | Время: 14.02.2019 - 09:09
from asyncio import sleep
from uuid import uuid4 as uuid

from discord import Member, Channel, VoiceClient, Server
from core.core import RounefordBot as Client

from core.api import BotPlugin, Priority
from core.objects import BotEmbed, BotColors


class AudioQueue:
    """
    Очередь из ytdl_player
    :add_audio_(): добавляет готовый класс QueueElement
    :add_audio(): добавляет лишь по аргументам

    :get_player(): получение ytdl_player по uuid()

    :remove_audio(): удаление ytdl_player из очереди путем поиска элемента
    :remove_audio_(): удаление ytdl_player по uuid()

    :get_next(): возврат следующего элемента (генератор)
    :get(): возврат ytdl_player по server.id
    :get_(): возврат ytdl_player по uuid()
    """

    def __init__(self, client: Client, server_id):
        self.client = client
        self.server_id = server_id
        self.queue = []

        self.current = None

    def get_next(self):
        if self.queue:
            yield self.queue.pop(0)

        yield None

    def add_audio_(self, audio):
        self.queue.append(audio)

        return audio

    def remove_audio(self, audio):
        if audio in self.queue:
            self.queue.remove(audio)

        return audio

    def remove_audio_(self, id_):
        players = [x for x in self.queue if x.id_ == id_]

        if not players:
            return None

        self.queue.remove(players[0])
        return players[0]

    def get_player(self, id_):
        players = [x for x in self.queue if x.id_ == id_]

        if not players:
            return None

        return players[0]

    def add_audio(self, id_, voice: VoiceClient, player, channel: Channel, server: Server, member: Member, url, title,
                  duration):
        self.queue.append(QueueElement(id_, voice, player, channel, server, member, url, title, duration))

        return QueueElement(id_, voice, player, channel, server, member, url, title, duration)

    def get_(self, id_):
        for player in self.queue:
            if player.id_ == id_:
                return player

        return None

    def get(self, id_):
        for player in self.queue:
            if player.server.id == id_:
                return player

        return None


class QueueElement:
    """
    Элемент очереди, содержащий информацию о текущем треке вместе с ytdl_player
    """

    def __init__(self, id_, voice, player, channel, server, member, url, title, duration):
        self.id_ = id_
        self.voice = voice
        self.player = player
        self.channel = channel
        self.server = server
        self.member = member
        self.url = url
        self.title = title
        self.duration = duration

    @property
    def to_json(self):
        return {
            "id": self.id_,
            "voice": self.voice,
            "player": self.player,
            "server": self.server,
            "channel": self.channel,
            "member": self.member,
            "url": self.url,
            "title": self.title,
            "duration": self.duration
        }


class AudioServers:
    def __init__(self, client: Client):
        self.client = client

        self.servers = []

    def get(self, server_id):
        elem_ = [x for x in self.servers if x.server_id == server_id]

        if elem_:
            return elem_[0]

        return None

    def set_current_player(self, server_id, player):
        queue = self.get(server_id)

        if queue:
            queue.current = player

        for index_, element in enumerate(self.servers):
            if element.server_id == server_id:
                self.servers[index_] = queue

        return queue

    def add_server(self, queue: AudioQueue):
        ids_ = [y.server_id for y in self.servers]

        if queue.server_id not in ids_:
            self.servers.append(queue)

        return queue

    def add_audio(self, server_id, audio: QueueElement):
        elem_ = [x for x in self.servers if x.server_id == server_id]

        if not elem_:
            return None

        elem_[0].add_audio_(audio)

        for index_, element in enumerate(self.servers):
            if element.server_id == server_id:
                self.servers[index_] = elem_[0]

        return elem_

    def remove_audio(self, server_id, audio: QueueElement):
        elem_ = [x for x in self.servers if x.server_id == server_id]

        if not elem_:
            return None

        elem_[0].remove_audio(audio)

        for index_, element in enumerate(self.servers):
            if element.server_id == server_id:
                self.servers[index_] = elem_[0]

        return elem_

    def remove_server(self, server_id):
        elem_ = [x for x in self.servers if x.server_id == server_id]

        if elem_:
            self.servers.remove(elem_[0])

        return elem_[0]


class AudioStreaming(BotPlugin):
    def __init__(self, client: Client):
        super().__init__(client)

        self.plugin_name = "Audio Streaming"
        self.version = "1.0.0"
        self.author = "https:;//github.com/Ar4ikov/"
        self.plugin_id = "audio_streaming"
        self.description = """Аудио-плагин, пользоляющий боту проигрывать музыку по запросам на различных серверах"""
        self.tasks = []
        self.priority = Priority.CORE_PLUGIN

        self.commands = {
            "play": "Поставить в очередь вашу музыкальную композицию для прослушивания",
            "pause": "Пауза текущей композиции",
            "skip": "Пропуск текущей композиции",
            "queue": "Очередь ожидания проигрывания композиций",
            "clean_queue": "Очистка очереди проигрывания композиций",
            "volume": "Общая громость звучания композиции",
            "leave": "Принудительно заставить бота выйти из голосового канала на сервере"
        }

        self.cache_dir = ".cache/youtube-dl/"

        self.voice = None
        self.player = None

        self.queue = AudioServers(self.client)

    def empty(self):
        return True

    async def player_task(self, server_id):
        while not self.queue.get(server_id).queue:
            pass

        while True:
            player = next(self.queue.get(server_id).get_next())

            if not player:
                self.queue.remove_server(server_id)
                break

            self.queue.set_current_player(server_id, player)

            await self.send_message(player.channel, embed=BotEmbed().set_settings(
                name="Сейчас играет `{}`".format(player.title),
                color=BotColors.RED.value
            ))

            self.queue.get(server_id).current.player.start()

            # Осторожно, костыль! Смотри какой торчит!
            while True:
                current_ = self.queue.get(server_id).current
                if not current_:
                    break

                if current_.player.is_done():
                    break

                await sleep(1)

    async def cmd_play(self, channel: Channel, member: Member, *args, **kwargs):
        voice_channel = member.voice.voice_channel

        if not voice_channel:
            await self.send_message(channel, embed=BotEmbed().set_settings(
                name="Вы не находитесь в голосовом канале!",
                desc="Вы должны находится в голосовом канале, чтобы сделать это!",
                color=BotColors.RED.value
            ))

            return True

        if not args:
            await self.send_message(channel, embed=BotEmbed().set_settings(
                name="Вы не указали название вашего трека!",
                color=BotColors.RED.value
            ))

            return True

        if not self.client.is_voice_connected(member.server):
            await self.client.join_voice_channel(voice_channel)

        voice: VoiceClient = self.client.voice_client_in(member.server)
        # print(voice)

        url = " ".join(args)

        await self.send_message(channel, embed=BotEmbed().set_settings(
            name="Ищу `{}`".format(url),
            color=BotColors.RED.value
        ))

        youtube_dl_before_ = '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'

        player = await voice.create_ytdl_player(
            url,
            before_options=youtube_dl_before_,
            ytdl_options={"default_search": "auto",
                          "cache_dir": self.cache_dir,
                          "is_playlist": True,
                          "enable_openssl": True})

        queue = self.queue.get(member.server.id)

        if not queue:
            self.queue.add_server(AudioQueue(self.client, member.server.id))
            self.client.logging.log(self, "[>] Создаю поток -> {}".format(member.server.id))

            self.queue.add_audio(
                member.server.id,
                QueueElement(uuid(), voice, player, channel, member.server, member, player.url, player.title,
                             player.duration))

            self.client.loop.create_task(self.player_task(member.server.id))
        else:
            self.queue.add_audio(
                member.server.id,
                QueueElement(uuid(), voice, player, channel, member.server, member, player.url, player.title,
                             player.duration))

        await self.send_message(channel, embed=BotEmbed().set_settings(
            name="Успешно добавлена песня `{}`".format(player.title),
            color=BotColors.RED.value,
        ))

    async def cmd_pause(self, channel: Channel, member: Member, *args, **kwargs):
        player = getattr(self.queue.get(member.server.id), "current", None)

        if player:
            player.player.pause()

        await self.send_message(channel, embed=BotEmbed().set_settings(
            name="⏸ Приостановлено",
            color=BotColors.GREEN.value
        ))

        return True

    async def cmd_resume(self, channel: Channel, member: Member, *args, **kwargs):
        player = getattr(self.queue.get(member.server.id), "current", None)

        if player:
            player.player.resume()

        await self.send_message(channel, embed=BotEmbed().set_settings(
            name="▶ Возобновлено!",
            color=BotColors.GREEN.value
        ))

        return True

    async def cmd_volume(self, channel: Channel, member: Member, *args, **kwargs):
        player = getattr(self.queue.get(member.server.id), "current", None)

        if not player:

            await self.send_message(channel, embed=BotEmbed().set_settings(
                name="🎧Сейчас не проигрывается ни одна песня, чтобы это сделать!",
                color=BotColors.RED.value
            ))

            return True

        if args:
            volume = float(args[0])
            player.player.volume = volume / 100 if volume <= 200 else 2
        else:
            await self.send_message(channel, embed=BotEmbed().set_settings(
                name="🎧Вы не указали значние громкости!",
                color=BotColors.RED.value
            ))

            return True

        await self.send_message(channel, embed=BotEmbed().set_settings(
            name="🎧 Текущий уровень громкости - {}%".format(args[0]),
            color=BotColors.GREEN.value
        ))

        return True

    async def cmd_skip(self, channel: Channel, member: Member, *args, **kwargs):
        player = getattr(self.queue.get(member.server.id), "current", None)

        if player:
            player.player.stop()
            self.queue.set_current_player(member.server.id, None)

        await self.send_message(channel, embed=BotEmbed().set_settings(
            name="⏭ Пропущено!",
            color=BotColors.GREEN.value
        ))

        return True

    async def cmd_clean_queue(self, channel: Channel, member: Member, *args, **kwargs):
        queue = self.queue.get(member.server.id)
        if queue:
            queue.queue.clear()

        await self.send_message(channel, embed=BotEmbed().set_settings(
            name="🗑️ Очищена очередь!",
            color=BotColors.GREEN.value
        ))

        return True

    async def cmd_queue(self, channel: Channel, member: Member, *args, **kwargs):

        queue = getattr(self.queue.get(member.server.id), "queue", [])

        out_ = ""
        for index_, audio in enumerate(queue):
            minutes, seconds = (audio.duration // 60, audio.duration % 60)
            if seconds < 10:
                seconds = "0{}".format(seconds)
            out_ += "`#{} - {}` by *{}* - `[{}]`\n".format(index_ + 1, audio.title, audio.member.name,
                                                           "{}:{}".format(minutes, seconds))

        fields = {}
        current = getattr(self.queue.get(member.server.id), "current", None)

        if current:
            fields["Сейчас играет"] = "`{}` by *{}*".format(current.title, current.member.name)

        fields["Очередь"] = out_ or "Очередь пуста :("

        await self.send_message(channel, embed=BotEmbed().set_settings(
            name="Очередь музыкальных композиций:",
            desc="{}queue - Вывод очереди треков".format(self.client.bot_tag),
            fields=fields,
            color=BotColors.WHITE.value
        ))

        return True

    async def cmd_leave(self, channel: Channel, member: Member, *args, **kwargs):
        await self.client.voice_client_in(member.server).disconnect()

    async def run(self):
        pass

# (self.voice, self.player, channel, member.server, member, self.player.url,
#                              self.player.title,
#                              self.player.duration)
# self.client.join_voice_channel(voice_channel)
