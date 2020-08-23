# igdb-pdt

Update RediSearch with IGDB data in the following Format:  

```json
{
  "game_id": {
    "name": "game_name",
    "cover": "igdb_coverart_url"
  }
}
```

## Usage

./populate-db

## Flags

`--mock`: gets data from data.json file instead of IGDB.  
`--persist`: save to RediSearch.  
`--output`: display data from IGDB in json format.  

## Environment Variables

`IGDB_API_KEY`: API key for IGDB. Required if not using mock file.  
`REDIS_HOSTNAME`: Hostname for Redis instance. Required.  
`REDIS_PORT`: Port of Redis. Defaults to 6379.  

## Docker image

Runs script every day at 2:30 AM via cronjob.
