# | Created by Ar4ikov
# | Время: 16.02.2019 - 16:49
from asyncio import sleep
from random import choice
from threading import Thread
from time import time

from discord import Channel, Member, Server, utils
from core.core import RounefordBot as Client
from flask import Flask, request, jsonify

from core.api import BotPlugin, Priority
from core.objects import BotEmbed, BotColors
from plugins.WebRequests.requests_ import *
from uuid import uuid4 as uuid

host = "127.0.0.1"


class Request:
    def __init__(self, type_, func, args=None, kwgs=None):
        self.type_ = type_ if type_ == "async" or type_ == "sync" else "sync"
        self.func = func

        self.args = args or []
        self.kwgs = kwgs or {}

        self.id_ = str(uuid())
        self.short_id_ = self.id_.replace("-", "")

    async def make(self):
        if self.type_ == "async":
            response = await self.func(*self.args, **self.kwgs)
            return response

        else:
            return self.func(*self.args, **self.kwgs)


class _Flask(Flask):
    def __init__(self, client=None, database_=None):
        super().__init__(__name__)

        self.client: WebRequests = client
        self.database = database_
        self.cursor = self.database.cursor()

    def run(self, host=None, port=None, debug=None,
            load_dotenv=True, **options):

        @self.route("/discord/", methods=["GET", "POST"])
        def discord_called():
            return jsonify({
                "app_name": "discord"
            }), 200

        @self.errorhandler(404)
        def call_method(e):

            method = request.path.split("/")[-1]
            data = request.data or request.args.to_dict() or request.json or request.form

            if method == "get_response":
                if "id" not in data:
                    return jsonify({
                        "status": "failed",
                        "error": "No id passed."
                    }), 204

                response_ = WebRequests.get_response(data.get("id"))

                if not response_:
                    return jsonify({
                        "status": "failed",
                        "error": "There is no requests with id = {}".format(data.get("id"))
                    }), 404

                return jsonify({
                    "status": "success",
                    "response": response_
                }), 200

            if "discord" not in request.path.split("/"):
                return jsonify({
                    "status": "failed",
                    "error": "App not found."
                }), 404

            if not getattr(self.client, method, None) and not getattr(self.client.client, method, None):
                return jsonify({
                    "status": "failed",
                    "error": "Method does not found."
                }), 404

            if "access_token" not in data:
                return jsonify({
                    "status": "failed",
                    "error": "Authorization failed. No access_token passed."
                }), 403

            access_token = data.get("access_token")
            resp = self.cursor.execute(
                """SELECT * FROM `access_tokens` WHERE `access_token` = '{}'""".format(access_token)).fetchone()

            if not resp:
                return jsonify({
                    "status": "failed",
                    "error": "Authorization error: wrong access_token."
                }), 403

            data.pop("access_token")

            if not data:
                return jsonify({
                    "status": "failed",
                    "error": "No data passed."
                }), 403

            if "server" in data:

                if data["server"] != resp[3]:
                    return jsonify({
                        "status": "failed",
                        "error": "Access denied: can't manage other servers."
                    }), 403

                data["server"] = self.client.client.get_server(data["server"])

            if "role" in data:
                if isinstance(data["server"], Server):
                    data["role"] = \
                        utils.get(self.client.client.get_server(data["server"].id).role_hierarchy, id=data["role"])

            if "channel" in data:
                data["channel"] = self.client.client.get_channel(data["channel"])

                if data["channel"]:
                    if str(data["channel"].id) not in [str(x.id) for x in
                                                       self.client.client.get_server(resp[1]).channels]:
                        return jsonify({
                            "status": "failed",
                            "error": "Access denied: can't manage channels in other servers."
                        }), 403

            request_ = WebRequests.append(
                Request(type_="async",
                        func=getattr(self.client, method, None) or getattr(self.client.client, method, None),
                        kwgs=data))

            return jsonify({
                "status": "success",
                "request_id": request_.short_id_
            }), 200

        super().run(host, port, debug, load_dotenv, **options)


class WebRequests(BotPlugin):
    requests = []
    responses = []

    def __init__(self, client: Client):
        super().__init__(client)

        self.plugin_name = "Web Requests"
        self.plugin_id = "web_requests"
        self.author = "https://github.com/Ar4ikov/"
        self.version = "1.0.0"
        self.tasks = ["request_handler", "flask_run"]
        self.description = """Обращение к боту через сервер на Flask"""
        self.priority = Priority.MEDIUM_PRIORITY

        self.host = host
        self.port = 80

        self.commands = {
            "generate_token": "Создание уникального токена сервера для запросов к боту через Web-интерфейс."
        }

        self.database = database
        self.cursor = self.database.cursor()

        self.flask = _Flask(self, self.database)

    @staticmethod
    async def background_request_handler():
        while True:
            await sleep(0.001)

            request_ = next(WebRequests.get_next())
            if request_:
                try:
                    await request_.make()
                    WebRequests.responses.append({"status": "ok", "id": request_.short_id_})

                except Exception as e:
                    WebRequests.responses.append(
                        {"status": "failed", "id": request_.short_id_, "runtime_error": str(e)})

    async def background_flask_run(self):
        tasks = [Thread(name="flask", target=self.flask.run, args=(self.host, self.port))]

        for task_ in tasks:
            task_.start()

    @staticmethod
    def get_response(id_):
        resp = [x for x in WebRequests.responses if x.get("id") == id_]

        if resp:
            WebRequests.responses.remove(resp[0])
            return resp[0]

        return None

    @staticmethod
    def generate_(length=64):
        matrix = list("abcdefghijklmopqrstuvwxyz0123456789")

        access_token = ""

        for i in range(length):
            access_token += choice(matrix)

        return access_token

    async def cmd_generate_token(self, channel: Channel, member: Member, *args, **kwargs):
        if channel.is_private:
            await self.send_message(channel, embed=BotEmbed().set_settings(
                name="Вы должны находится на сервере, прежде чем это сделать!",
                color=BotColors.RED.value
            ))

            return True

        if not member.server_permissions.administrator:
            await self.send_message(channel, embed=BotEmbed().set_settings(
                name="У вас недостаточно прав, чтобы сделать это.",
                color=BotColors.RED.value
            ))

            return True

        access_token_ = self.cursor.execute("""SELECT * FROM `access_tokens` WHERE `server_id` = '{}'""".format(
            member.server.id
        )).fetchone()

        access_token = self.generate_()

        if not access_token_:
            self.cursor.execute(
                """
                INSERT INTO `access_tokens` (`server_id`, `member_id`, `access_token`, `when_created`) 
                VALUES ('{}', '{}', '{}', '{}') 
                """.format(member.server.id, member.id, access_token, time()))
            self.database.commit()
        else:
            print("updating", member.server.id)
            self.cursor.execute(
                """UPDATE `access_tokens` SET `access_token` = '{}', `when_created` = '{}' WHERE `server_id` = '{}'
                """.format(
                    access_token,
                    str(time())[:10],
                    member.server.id,
                ))
            self.database.commit()

        await self.send_message(channel, embed=BotEmbed().set_settings(
            name="Ваш Access-Token - `{}`".format(access_token),
            desc="Никому не давайте ваш Access-Token и исполняйте данную команду толкьо в защищённых каналах!",
            color=BotColors.RED.value
        ))

        return True

    @staticmethod
    def append(event):
        WebRequests.requests.append(event)

        return event

    @staticmethod
    def get_next():
        if WebRequests.requests:
            yield WebRequests.requests.pop(0)

        else:
            yield None

    async def run(self, **kwargs):
        pass
