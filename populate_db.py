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
import time

BASE_URL = 'https://api.igdb.com/v4/games'
CLIENT_ID = ''
CLIENT_SECRET = ''
REDIS_HOSTNAME = 'localhost'
REDIS_PORT = 6379
IGDB_SRC = 'API'
if 'REDIS_HOSTNAME' in os.environ:
    REDIS_HOSTNAME = os.environ['REDIS_HOSTNAME']
if 'REDIS_PORT' in os.environ:
    REDIS_PORT = os.environ['REDIS_PORT']
if 'AUTHORIZATION' in os.environ:
    AUTHORIZATION = os.environ['AUTHORIZATION']
if 'CLIENT_ID' in os.environ:
    CLIENT_ID = os.environ['CLIENT_ID']
if 'CLIENT_SECRET' in os.environ:
    CLIENT_SECRET = os.environ['CLIENT_SECRET']
if 'IGDB_SRC' in os.environ:
    IGDB_SRC = os.environ['IGDB_SRC']

auth_headers = {'Client-ID': CLIENT_ID, 'Authorization': ''}

GAME_QUERY_STRING = b'fields id, summary, slug, name, alternative_names.name, cover.url; where (multiplayer_modes.onlinecoop=true | \
                 multiplayer_modes.offlinecoop=true | multiplayer_modes.lancoop=true | \
                 game_modes = (2, 6)) & category=(0,9);'


async def set_authorization(
    session: aiohttp.ClientSession
) -> dict:
    if not (CLIENT_ID and CLIENT_SECRET):
        print('CLIENT_ID and CLIENT_SECRET environment variables not set!')
        return
    url = 'https://id.twitch.tv/oauth2/token?client_id=%s&client_secret=%s&grant_type=client_credentials' % (CLIENT_ID, CLIENT_SECRET)
    resp = await session.post(url=url)
    data = await resp.json()
    access_token = data['access_token']
    auth_headers['Authorization'] = 'Bearer %s' % access_token


async def get_count(
    session: aiohttp.ClientSession
) -> dict:
    url = BASE_URL + '/count'
    resp = await session.post(url=url, headers=auth_headers,
                              data=GAME_QUERY_STRING)
    data = await resp.json()
    count = data['count']
    return count


async def get_games(
    session: aiohttp.ClientSession,
    offset: int,
    max_id: int
) -> dict:
    url = BASE_URL
    resp = await session.post(url=url, headers=auth_headers,
                              data=GAME_QUERY_STRING[:-1] +
                              b' & id>%d;limit 500;offset %d;' % (max_id, offset))
    data = await resp.json()
    return data


def get_cover(data: dict):
    if 'cover' in data:
        return data['cover']['url'].replace('t_thumb', 't_cover_big')
    return ''


async def fetch_games():
    async with aiohttp.ClientSession() as session:
        await set_authorization(session=session)
        if not auth_headers['Authorization']:
            print('Failed to set Authorization!')
            return json.dumps({}, indent=4)
        count = await get_count(session=session)
        max_id = -1
        data = {}
        last_time = 0
        for _ in range(0, count, 2000):
            new_time = time.time_ns()
            while new_time - last_time < 1000000000:
                time.sleep(5000/1000000000.0)
                new_time = time.time_ns()
            last_time = new_time
            tasks = [get_games(session=session, offset=i, max_id=max_id) for i in range(0, 2000, 500)]
            new_data = await asyncio.gather(*tasks, return_exceptions=True)
            new_data = list(itertools.chain(*new_data))
            max_entry = max(new_data, key=lambda d: d['id'])
            max_id = int(max_entry['id'])
            new_data = {
                p['slug']: {
                    'name': p['name'],
                    'alt_names': [*map(lambda v: v.get('name', ''), p.get('alternative_names', []))],
                    'summary': p.get('summary', False) or '',
                    'thumb':  p.get('cover', {}).get('url', '') or '',
                    'cover': get_cover(p),
                }
                for p in new_data}
            data = {**data, **new_data}
        return data


def load_mock_data():
    with open('data.json') as f:
        data = json.load(f)
    return data


def cache_to_redis(data: dict):
    if REDIS_HOSTNAME == '':
        print('REDIS_HOSTNAME environment variable is not set')
        return
    client = Client('games', host=REDIS_HOSTNAME, port=REDIS_PORT)
    indexCreated = False
    maxAltNames = len(max(data.values(), key=lambda d: len(d['alt_names']))['alt_names'])
    while not indexCreated:
        try:
            client.create_index([TextField('name', weight=10),
                                *[TextField('alt_name_%d' % i, weight=10) for i in range(maxAltNames)],
                                TextField('summary', weight=1)],
                                TextField('cover', weight=0),
                                TextField('thumb', weight=0))
            indexCreated = True
        except Exception:
            print('Failed to create index, retrying %s')
            time.sleep(3)

    for k, v in data.items():
        client.add_document(k,
                            name=v['name'],
                            **{'alt_name_%d' % i: n for i, n in enumerate(v['alt_names'])},
                            cover=v['cover'],
                            thumb=v['thumb'],
                            summary=v['summary'])
    print('done')


def main(args: dict):
    if (not args.output):
        print('igdb redis updating: ', datetime.now())
    if IGDB_SRC == 'MOCK' or args.mock:
        data = load_mock_data()
    else:
        data = asyncio.run(fetch_games())
    if args.output:
        print(json.dumps(data, indent=4))
    else:
        print('call complete. fetched %d games' % (len(data)))
    if args.persist:
        cache_to_redis(data=data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='load redis db with game name list')
    parser.add_argument('--mock', action='store_true')
    parser.add_argument('--persist', action='store_true')
    parser.add_argument('--output', action='store_true')
    arguments = parser.parse_args()
    main(args=arguments)
