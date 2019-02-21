# | Created by Ar4ikov
# | Время: 17.02.2019 - 09:18
from asyncio import sleep
from time import time

from discord import Message, Member, Channel, utils, AppInfo
from discord.ext.commands import Bot as Client

from core.api import BotPlugin, Priority
from core.objects import BotEmbed, BotColors
from plugins.Essentials.requests_ import *


class Essentials(BotPlugin):
    def __init__(self, client: Client):
        super().__init__(client)

        self.plugin_name = "Essentials"
        self.version = "1.0.0"
        self.author = "https://github.com/Ar4ikov"
        self.plugin_id = "essentials"
        self.priority = Priority.MEDIUM_PRIORITY
        self.description = """Полезные команды, упрощающие жизнь модерации на сервере"""

        self.database = database
        self.cursor = cursor

        self.commands = {
            "kick": "Кикнуть участника с сервера",
            "mute": "Замутить участника",
            "ban": "Забанить участника",
            "unmute": "Размутить участника",
            "set_mute_role": "Установить роль для выдачи мута"
        }
        self.tasks = ["start_mute_checking"]

    async def unmute_after(self, time_, member, role_id):
        await sleep(time_)
        self.cursor.execute("""DELETE FROM `mutes` WHERE `member_id` = '{}' AND `server_id` = '{}';""".format(
            member.id, member.server.id
        ))
        self.database.commit()

        await self.client.remove_roles(member, utils.get(member.server.role_hierarchy, id=str(role_id)))

    async def background_start_mute_checking(self):
        await self.client.wait_until_ready()

        resp = self.cursor.execute("""SELECT * FROM `mutes`""").fetchall()

        for item in resp:
            time_ = int(str(time())[:10])
            member_ = self.client.get_server(item[1]).get_member(item[2])
            role_id = self.cursor.execute(
                """SELECT * FROM `mute_roles` WHERE `server_id` = '{}'""".format(member_.server.id)).fetchone()[2]

            if item[5] != "never":
                if time_ - item[4] < item[5]:
                    self.client.loop.create_task(self.unmute_after(
                        time_ - item[4], member_, role_id
                    ))
                else:
                    self.cursor.execute("""DELETE FROM `mutes` WHERE `id` = '{}';""".format(item[0]))
                    self.database.commit()

                    await self.client.remove_roles(
                        member_,
                        utils.get(member_.server.role_hierarchy, id=str(role_id))
                    )

    async def cmd_mute(self, channel: Channel, member: Member, *args, **kwargs):

        role_id = self.cursor.execute("""
        SELECT * FROM `mute_roles` WHERE `server_id` = '{}'""".format(member.server.id)).fetchone()

        if not role_id:
            await self.send_message(channel, embed=BotEmbed().set_settings(
                name="Для начала, выберете роль, которую бот будет выдавать при муте. Просто укажите её\n"
                     "`{}set_mute_role <роль>`".format(self.client.bot_tag),
                color=BotColors.RED.value
            ))

            return True

        mute_dict = {}

        signs = [[
            ["w", "week", "weeks", "неделя", "недель"],
            ["d", "days", "day", "дней", "д"],
            ["h", "hour", "hours", "ч", "час", "часов"],
            ["m", "minute", "minutes", "м", "минута", "минуты", "минут"],
            ["s", "sec", "secs", "seconds", "second", "с", "сек", "секунда", "секунд", "секунды"]
        ], [86400 * 7, 86400, 3600, 60, 1]]

        for index_, sign in enumerate(signs[0]):
            time__ = signs[1][index_]

            for element in sign:
                mute_dict[element] = time__

        if not member.server_permissions.kick_members:
            await self.send_message(channel, embed=BotEmbed().set_settings(
                name="У вас недостаточно прав, чтобы сделать это!",
                color=BotColors.RED.value
            ))

            return True

        if not args:
            await self.send_message(channel, embed=BotEmbed().set_settings(
                name="Вы не указали ни одного учатсника, чтобы сделать это!",
                color=BotColors.RED.value
            ))

            return True

        member_id = args[0].replace(">", "").replace("<", "").replace("!", "").replace("@", "")

        if member_id == member.id:
            await self.send_message(channel, embed=BotEmbed().set_settings(
                name="Вы не можете заиутить самого себя. Но вам нужен для этого скотч!",
                color=BotColors.RED.value
            ))

            return True

        resp_ = self.cursor.execute("""SELECT * FROM `mutes` WHERE `member_id` = '{}'""".format(member_id)).fetchone()
        if resp_:
            await self.send_message(channel, embed=BotEmbed().set_settings(
                name="Данный участник уже находится в муте!",
                color=BotColors.RED.value
            ))

            return True

        member_: Member = member.server.get_member(member_id)
        bot = await self.client.application_info()

        if not member_:
            await self.send_message(channel, embed=BotEmbed().set_settings(
                name="Данный участник не состоит в этом сервере!",
                color=BotColors.RED.value
            ))

            return True

        if not member.server.get_member(bot.id).server_permissions.kick_members or member.server.get_member(
                bot.id).top_role < member_.top_role:
            await self.send_message(channel, embed=BotEmbed().set_settings(
                name="У Бота недостаточно прав, чтобы сделать это. Если вы администратор сервера, наделите "
                     "бота таковыми правами.",
                color=BotColors.RED.value
            ))

            return True

        time_ = []

        if len(args) > 1:
            time_ = args[1].split(":")

        args_ = []
        for i in [y for y in [x.split("-") for x in time_]]:
            for elem in i:
                args_.append(elem)

        if time_:
            if len(args_) // len(time_) != 2:
                await self.send_message(channel, embed=BotEmbed().set_settings(
                    name="Неверный синтаксис указания времени. Если вы желаете указать время мута, то взгляните на "
                         "пример "
                         "ниже: ",
                    fields={
                        "{tag}mute @Member `10-s`\n"
                        "{tag}mute @Member `20-d:10-s`\n"
                        "{tag}mute @Member `20-дней:15-часов`".format(tag=self.client.bot_tag): "-----"
                    },
                    color=BotColors.RED.value
                ))

                return True

        mute_time = None

        if time_:
            mute_time = sum([mute_dict.get(x.split("-")[1]) * int(x.split("-")[0]) or 0 for x in time_])

        if mute_time:
            self.client.loop.create_task(self.unmute_after(mute_time, member_, role_id[2]))

        await self.client.add_roles(member_, utils.get(member.server.role_hierarchy, id=str(role_id[2])))

        self.cursor.execute(
            """INSERT INTO `mutes` (`server_id`, `member_id`, `muted_by`, `when_muted`, `mute_reset_after`) 
            VALUES ('{}', '{}', '{}', '{}', '{}')""".format(
                member.server.id, member_id, member.id, str(time())[:10], mute_time or "never"
            ))
        self.database.commit()

        await self.send_message(channel, embed=BotEmbed().set_settings(
            name="Успешно выдан мут участнику `@{}` на {} секунд".format(member_.name, mute_time or "∞"),
            color=BotColors.GREEN.value
        ))

        return True

    async def cmd_unmute(self, channel: Channel, member: Member, *args, **kwargs):
        role_id = self.cursor.execute("""
                SELECT * FROM `mute_roles` WHERE `server_id` = '{}'""".format(member.server.id)).fetchone()

        if not role_id:
            await self.send_message(channel, embed=BotEmbed().set_settings(
                name="Для начала, выберете роль, которую бот будет выдавать при муте. Просто укажите её\n"
                     "`{}mute <роль>`".format(self.client.bot_tag),
                color=BotColors.RED.value
            ))

            return True

        if not member.server_permissions.ban_members:
            await self.send_message(channel, embed=BotEmbed().set_settings(
                name="У вас недостаточно прав, чтобы сделать это!",
                color=BotColors.RED.value
            ))

            return True

        if not args:
            await self.send_message(channel, embed=BotEmbed().set_settings(
                name="Вы не указали ни одного учатсника, чтобы сделать это!",
                color=BotColors.RED.value
            ))

            return True

        member_id = args[0].replace(">", "").replace("<", "").replace("!", "").replace("@", "")

        if member_id == member.id:
            await self.send_message(channel, embed=BotEmbed().set_settings(
                name="Вы не можете заиутить самого себя. Но вам нужен для этого скотч!",
                color=BotColors.RED.value
            ))

            return True

        resp_ = self.cursor.execute("""SELECT * FROM `mutes` WHERE `member_id` = '{}'""".format(member_id)).fetchone()
        if not resp_:
            await self.send_message(channel, embed=BotEmbed().set_settings(
                name="Данный участник не находится в муте!",
                color=BotColors.RED.value
            ))

            return True

        member_: Member = member.server.get_member(member_id)
        bot = await self.client.application_info()

        if not member_:
            await self.send_message(channel, embed=BotEmbed().set_settings(
                name="Данный участник не состоит в этом сервере!",
                color=BotColors.RED.value
            ))

            return True

        if not member.server.get_member(bot.id).server_permissions.kick_members or member.server.get_member(
                bot.id).top_role < member_.top_role:
            await self.send_message(channel, embed=BotEmbed().set_settings(
                name="У Бота недостаточно прав, чтобы сделать это. Если вы администратор сервера, наделите "
                     "бота таковыми правами.",
                color=BotColors.RED.value
            ))

            return True

        await self.client.remove_roles(member_, utils.get(member.server.role_hierarchy, id=str(role_id[2])))

        self.cursor.execute("""DELETE FROM `mutes` WHERE `member_id` = '{}' AND `server_id` = '{}'""".format(
            member_id, member_.server.id
        ))

        self.database.commit()

        await self.send_message(channel, embed=BotEmbed().set_settings(
            name="Мут успешно снят с участника @{}".format(member_.name),
            color=BotColors.GREEN.value
        ))

        return True

    async def cmd_ban(self, channel: Channel, member: Member, *args, **kwargs):
        if not member.server_permissions.ban_members:
            await self.send_message(channel, embed=BotEmbed().set_settings(
                name="У вас недостаточно прав, чтобы сделать это!",
                color=BotColors.RED.value
            ))

            return True

        bot: AppInfo = await self.client.application_info()

        if not args:
            await self.send_message(channel, embed=BotEmbed().set_settings(
                name="Вы не указали ни одного учатсника, чтобы сделать это!",
                color=BotColors.RED.value
            ))

            return True

        member_id = args[0].replace(">", "").replace("<", "").replace("!", "").replace("@", "")

        if member_id == member.id:
            await self.send_message(channel, embed=BotEmbed().set_settings(
                name="Вы не можете забанить самого себя. Ну, только в ГУЛАГ, разве что, отправитесь.",
                color=BotColors.RED.value
            ))

            return True

        member_: Member = member.server.get_member(member_id)
        if not member_:
            await self.send_message(channel, embed=BotEmbed().set_settings(
                name="Данный участник не состоит в этом сервере!",
                color=BotColors.RED.value
            ))

            return True

        if not member.server.get_member(bot.id).server_permissions.ban_members or member.server.get_member(
                bot.id).top_role < member_.top_role:
            await self.send_message(channel, embed=BotEmbed().set_settings(
                name="У Бота недостаточно прав, чтобы сделать это. Если вы администратор сервера, наделите "
                     "бота таковыми правами.",
                color=BotColors.RED.value
            ))

            return True

        await self.client.kick(member_)
        await self.send_message(channel, embed=BotEmbed().set_settings(
            name="Успешно забанен участник `@{}`".format(member_.name),
            color=BotColors.GREEN.value
        ))

        return True

    async def cmd_kick(self, channel: Channel, member: Member, *args, **kwargs):
        if not member.server_permissions.kick_members:
            await self.send_message(channel, embed=BotEmbed().set_settings(
                name="У вас недостаточно прав, чтобы сделать это!",
                color=BotColors.RED.value
            ))

            return True

        bot: AppInfo = await self.client.application_info()

        if not args:
            await self.send_message(channel, embed=BotEmbed().set_settings(
                name="Вы не указали ни одного учатсника, чтобы сделать это!",
                color=BotColors.RED.value
            ))

            return True

        member_id = args[0].replace(">", "").replace("<", "").replace("!", "").replace("@", "")

        if member_id == member.id:
            await self.send_message(channel, embed=BotEmbed().set_settings(
                name="Вы не можете кикнуть самого себя. Или вы действительно конченный?",
                color=BotColors.RED.value
            ))

            return True

        member_: Member = member.server.get_member(member_id)
        if not member_:
            await self.send_message(channel, embed=BotEmbed().set_settings(
                name="Данный участник не состоит в этом сервере!",
                color=BotColors.RED.value
            ))

            return True

        if not member.server.get_member(bot.id).server_permissions.kick_members or member.server.get_member(
                bot.id).top_role < member_.top_role:
            await self.send_message(channel, embed=BotEmbed().set_settings(
                name="У Бота недостаточно прав, чтобы сделать это. Если вы администратор сервера, наделите "
                     "бота таковыми правами.",
                color=BotColors.RED.value
            ))

            return True

        await self.client.ban(member_)
        await self.send_message(channel, embed=BotEmbed().set_settings(
            name="Успешно кикнут участник `@{}`".format(member_.name),
            color=BotColors.GREEN.value
        ))

        return True

    async def cmd_set_mute_role(self, channel: Channel, member: Member, *args, **kwargs):
        if not member.server_permissions.administrator:
            await self.send_message(channel, embed=BotEmbed().set_settings(
                name="У вас недостаточно прав, чтобы сделать это!",
                color=BotColors.RED.value
            ))

            return True

        bot: AppInfo = await self.client.application_info()

        if not args:
            await self.send_message(channel, embed=BotEmbed().set_settings(
                name="Вы должны указать роль, которую хотите сделать в качестве выдаваемой при муте участника",
                color=BotColors.RED.value
            ))

            return True

        role_id = args[0].replace("@", "").replace("&", "").replace("<", "").replace(">", "")

        role_ = utils.get(member.server.role_hierarchy, id=str(role_id))

        if not role_:
            await self.send_message(channel, embed=BotEmbed().set_settings(
                name="Неверный Id роли!",
                color=BotColors.RED.value
            ))

            return True

        resp_ = self.cursor.execute("""
        SELECT * FROM `mute_roles` WHERE `server_id` = '{}'""".format(member.server.id)).fetchone()

        if not resp_:
            self.cursor.execute("""INSERT INTO `mute_roles` (`server_id`, `role_id`, `created_by`) 
            VALUES ('{}', '{}', '{}');""".format(member.server.id, role_id, member.id))
        else:
            self.cursor.execute("""UPDATE `mute_roles` SET `role_id` = '{}' WHERE `server_id` = '{}'""".format(
                role_id, member.server.id
            ))

        self.database.commit()
        await self.send_message(channel, embed=BotEmbed().set_settings(
            name="Успешно добавлена роль @{}".format(role_.name),
            desc="Теперь при выдаче участнику мута, бот будет автоматически выдавать ему эту роль",
            color=BotColors.GREEN.value
        ))

        return True

    async def run(self):
        pass
