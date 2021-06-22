import asyncio
import aioredis
import argparse
import trio

from contextlib import asynccontextmanager
from trio_asyncio import run, aio_as_trio
from db import Database


class TrioDatabase(Database):

    async def add_sms_mailing(self, sms_id, phones, text, created_at=None):
        await aio_as_trio(super().add_sms_mailing)(sms_id, phones, text, created_at)

    async def list_sms_mailings(self):
        return await aio_as_trio(super().list_sms_mailings)()

    async def get_pending_sms_list(self):
        return await aio_as_trio(super().get_pending_sms_list)()

    async def update_sms_status_in_bulk(self, sms_list):
        await aio_as_trio(super().update_sms_status_in_bulk)(sms_list)

    async def get_sms_mailings(self, *sms_ids):
        return await aio_as_trio(super().get_sms_mailings)(*sms_ids)


def create_argparser():
    parser = argparse.ArgumentParser(description='Redis database usage example')
    parser.add_argument('--address', action='store', dest='redis_uri', help='Redis URI')
    parser.add_argument('--password', action='store', dest='redis_password', help='Redis db password')

    return parser


@asynccontextmanager
async def handle_redis_conn(args):
    print(args.redis_uri)
    redis = await aio_as_trio(aioredis.create_redis_pool)(
        args.redis_uri,
        password=args.redis_password,
        encoding='utf-8',
    )

    try:
        yield redis

    finally:
        redis.close()
        await aio_as_trio(redis.wait_closed)()


async def main():
    asyncio._set_running_loop(asyncio.get_event_loop())

    parser = create_argparser()
    args = parser.parse_args()

    async with handle_redis_conn(args) as redis:
        db = TrioDatabase(redis)

        sms_id = '1'
        phones = [
            '+7 999 519 05 57',
            '911',
            '112',
        ]
        text = 'Вечером будет шторм!'

        await db.add_sms_mailing(sms_id, phones, text)

        sms_ids = await db.list_sms_mailings()
        print('Registered mailings ids', sms_ids)

        pending_sms_list = await db.get_pending_sms_list()
        print('pending:')
        print(pending_sms_list)

        await db.update_sms_status_in_bulk([
            # [sms_id, phone_number, status]
            [sms_id, '112', 'failed'],
            [sms_id, '911', 'pending'],
            [sms_id, '+7 999 519 05 57', 'delivered'],
            # following statuses are available: failed, pending, delivered
        ])

        pending_sms_list = await db.get_pending_sms_list()
        print('pending:')
        print(pending_sms_list)

        sms_mailings = await db.get_sms_mailings('1')
        print('sms_mailings')
        print(sms_mailings)

        async def send():
            while True:
                await trio.sleep(1)
                await aio_as_trio(redis.publish)('updates', sms_id)

        async def listen():
            *_, channel = await aio_as_trio(redis.subscribe)('updates')

            while True:
                raw_message = await aio_as_trio(channel.get)()
                if not raw_message:
                    raise ConnectionError('Connection was lost')

                message = raw_message.decode('utf-8')
                print('Got message:', message)

        async with trio.open_nursery() as nursery:
            nursery.start_soon(send)
            nursery.start_soon(listen)


if __name__ == '__main__':
    run(main)
