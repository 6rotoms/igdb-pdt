# igdb-pdt

Update RediSearch with IGDB data in the following Format:  
```json
{
  "game_slug": {
    "name": "game_name",
    "cover": "igdb_coverart_url",
    "thumb": "igdb_thumbart_url",
    "summary": "summary text",
    "alt_names_%i": "alt_name_i"
  }
}
```

*__Note__: Only the name, alt_names, and summary are used as fields that impact the search, with weights 10, 10, and 1 respectively.*  

## Usage

`CLIENT_ID=client_id; CLIENT_SECRET=client_secret; ./populate_db.py`  

## Flags

`--mock`: gets data from data.json file instead of IGDB.  
`--persist`: save to RediSearch.  
`--output`: display data from IGDB to console. (used for creating mock data.json via `./populate_db.py --output > data.json`)  

## Environment Variables

`CLIENT_ID`: Client ID for IGDB. Required if not using mock file.  
`CLIENT_SECRET`: Client Secret for IGDB. Required if not using mock file.  
`REDIS_HOSTNAME`: Hostname for Redis instance. Required.  
`REDIS_PORT`: Port of Redis. Defaults to 6379.  

## Docker image

Runs script every day at 2:30 AM via cronjob.

## TODO
- [ ] add support for caching authorization token, and only refreshing if expired, otherwise keep it
- [ ] seperate logging and output