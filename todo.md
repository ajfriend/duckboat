# function for loading data with remote

idea:

```python
dw.Table(
    'data/yellow_tripdata_2010-01.parquet',
    remote='https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2010-01.parquet',
)
```

try looking for file `data/yellow_tripdata_2010-01.parquet`. If no file exists, look at the remote, download the file, save it as the given filename, and then load from the given filename.