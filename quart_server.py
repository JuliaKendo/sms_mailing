import aioredis
import asyncio
import json
import trio

from db import Database
from environs import Env
from quart import render_template, request, websocket, jsonify
from quart_trio import QuartTrio
from hypercorn.trio import serve
from hypercorn.config import Config as HyperConfig
from trio_asyncio import open_loop, aio_as_trio
from smsc_api import send_sms
from smsc_lib import decode_message


env = Env()
env.read_env()
app = QuartTrio(__name__)


@app.before_serving
async def initiate_mailing():
    asyncio._set_running_loop(asyncio.get_event_loop())
    app.db_pool = await aio_as_trio(aioredis.create_redis_pool)(
        f'redis://{env("REDIS_HOST")}:{env("REDIS_PORT")}',
        password=env('REDIS_PASSWORD'),
        encoding='utf-8',
    )
    app.db = Database(app.db_pool)


@app.after_serving
async def close_mailing():
    app.db_pool.close()
    await aio_as_trio(app.db_pool.wait_closed)()


@app.route('/')
async def index():
    return await render_template('index.html')


@app.route('/send/', methods=['POST'])
async def handle_front_message():
    message = await request.get_data()
    decoded_message = decode_message(message)
    dispatch_report = await aio_as_trio(send_sms)(
        env('SMSC_LOGIN'),
        env('SMSC_PSW'),
        env.list('PHONE_NUMBERS'),
        decoded_message
    )
    if dispatch_report:
        await aio_as_trio(app.db.add_sms_mailing)(
            dispatch_report['id'], dispatch_report['phones'], dispatch_report['message']
        )
    return jsonify(True)


@app.websocket('/ws')
async def ws():
    msg = {
        'msgType': 'SMSMailingStatus',
        'SMSMailings': []
    }
    sms_ids = await aio_as_trio(app.db.list_sms_mailings)()
    for sms_id in sms_ids:
        sms_mailings = await aio_as_trio(app.db.get_sms_mailings)(sms_id)
        for sms_mailing in sms_mailings:
            msg['SMSMailings'] = [{
                "timestamp": sms_mailing['created_at'],
                "SMSText": sms_mailing['text'],
                "mailingId": sms_id,
                #  TODO: добавить статистику по количеству sms
                "totalSMSAmount": 1,
                "deliveredSMSAmount": 0,
                "failedSMSAmount": 0,
            }, ]
            await websocket.send(json.dumps(msg))


async def run_server():
    async with open_loop():
        config = HyperConfig()
        config.bind = env.list('HOSTS', ['127.0.0.1:5000'])
        config.use_reloader = True

        await serve(app, config)


if __name__ == '__main__':
    trio.run(run_server)
