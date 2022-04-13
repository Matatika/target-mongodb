"""MongoDB target stream class, which handles writing streams."""

from typing import Any, Dict, List, Tuple, Union

from singer_sdk.sinks import BatchSink

import requests
import urllib.parse
import datetime
import pymongo
from bson.objectid import ObjectId

class MongoDbSink(BatchSink):
    """MongoDB target sink class."""

    max_size = 10

    def process_batch(self, context: dict) -> None:
        """Write out any prepped records and return once fully written."""
        # The SDK populates `context["records"]` automatically
        # since we do not override `process_record()`.

        # get connection configs
        connection_string = self.config.get("connection_string")
        db_name = self.config.get("db_name")
        # set the collection based on current stream
        collection = urllib.parse.quote(self.stream_name)

        client = pymongo.MongoClient(connection_string, connectTimeoutMS=2000, retryWrites=True)
        db = client[db_name]

        records = context["records"]
        primary_id = self.key_properties[0]

        for record in records:
            find_id = record[primary_id]
            # pop the key from update if primary key is _id
            if primary_id == '_id':
                find_id = ObjectId(find_id)
                record.pop("_id")

            # Last parameter True is upsert which inserts a new record if it doesnt exists or replaces current if found
            db[collection].update_one({primary_id: find_id}, {"$set": record}, True)

        self.logger.info(f"Uploaded {len(records)} records into {collection}")

        # Clean up records
        context["records"] = []
