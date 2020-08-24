#!/usr/bin/env python3
"""
load redis db with game name data
"""
import asyncio
import aiohttp
import itertools
import json
import argparse
from redisearch import Client, TextField
import os
from datetime import datetime

USER_KEY = 'de3df3e4c967363b9ef0ecfd68ee89e6'
REDIS_HOSTNAME = ''
REDIS_PORT = 6379
IGDB_SRC = 'API'
if 'REDIS_HOSTNAME' in os.environ:
    REDIS_HOSTNAME = os.environ['REDIS_HOSTNAME']
if 'REDIS_PORT' in os.environ:
    REDIS_PORT = os.environ['REDIS_PORT']
if 'IGDB_API_KEY' in os.environ:
    USER_KEY = os.environ['IGDB_API_KEY']
if 'IGDB_SRC' in os.environ:
    IGDB_SRC = os.environ['IGDB_SRC']

GAME_QUERY_STRING = b'fields id, name, cover.url; where (multiplayer_modes.onlinecoop=true | \
                 multiplayer_modes.offlinecoop=true | multiplayer_modes.lancoop=true | \
                 game_modes = (2, 6));'


async def get_count(
    session: aiohttp.ClientSession
) -> dict:
    url = "https://api-v3.igdb.com/games/count"
    resp = await session.post(url=url, headers={"user-key": USER_KEY},
                              data=GAME_QUERY_STRING)
    data = await resp.json()
    count = data['count']
    print(f"Received data for {count} multiplayer games")
    return count


async def get_games(
    session: aiohttp.ClientSession,
    offset: int,
    max_id: int
) -> dict:
    url = "https://api-v3.igdb.com/games"
    resp = await session.post(url=url, headers={"user-key": USER_KEY},
                              data=GAME_QUERY_STRING[:-1] + b' & id>%d;limit 500;offset %d;' % (max_id, offset))
    data = await resp.json()
    return data


def get_cover(data: dict):
    if 'cover' in data:
        return data['cover']['url'].replace('t_thumb', 't_cover_big')
    return ''


async def fetch_games():
    async with aiohttp.ClientSession() as session:
        count = await get_count(session=session)
        max_id = -1
        data = {}
        for i in range(0, count, 5000):
            tasks = []
            for i in range(0, 5000, 500):
                tasks.append(get_games(session=session, offset=i, max_id=max_id))
            new_data = await asyncio.gather(*tasks, return_exceptions=True)
            new_data = list(itertools.chain(*new_data))
            max_entry = max(new_data, key=lambda d: d['id'])
            max_id = int(max_entry['id'])
            new_data = {p['id']: {'name': p['name'], 'cover': get_cover(p)} for p in new_data}
            data = {**data, **new_data}
        return json.dumps(data, indent=4)


def load_mock_data():
    with open('data.json') as f:
        data = json.load(f)
    return data


def cache_to_redis(data: dict):
    if REDIS_HOSTNAME == '':
        print('REDIS_HOSTNAME environment variable is not set')
        return
    client = Client('games', host='redis', port=REDIS_PORT)
    client.create_index([TextField('name')], TextField('cover', weight=0))
    for k, v in data.items():
        client.add_document(k, name=v['name'], cover=v['cover'])
    print('done')


def main(args: dict):
    print('igdb redis updating: ', datetime.now())
    if IGDB_SRC == 'MOCK' or args.mock:
        data = load_mock_data()
    else:
        data = asyncio.run(fetch_games())
    if args.output:
        print(data)
    if args.persist:
        cache_to_redis(data=data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='load redis db with game name list')
    parser.add_argument('--mock', action='store_true')
    parser.add_argument('--persist', action='store_true')
    parser.add_argument('--output', action='store_true')
    arguments = parser.parse_args()
    main(args=arguments)
