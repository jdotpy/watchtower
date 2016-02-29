from pymongo import MongoClient
from ..checks import BaseCheck
from ..utils import index_queryset

class MongoStorage():
    def __init__(self, **options):
        self.host = options.get('host', 'localhost')
        self.port = options.get('port', None)
        self.user = options.get('user', None)
        self.password = options.get('password', None)
        self.db_name = options.get('database', 'watchtower')
        self.collection_name = options.get('collection', 'log')
        self.client = MongoClient(self.host, self.port)
        self.db = self.client[self.db_name]
        self.collection = self.db[self.collection_name]

    def log_result(self, key, timestamp, status):
        self.collection.insert_one({
            'key': key,
            'timestamp': timestamp,
            'status': status
        })

    def reset(self):
        result = self.collection.delete_many({})

    def summary(self, keys):
        results = {}
        last_successes = self.collection.aggregate(
            [
                {
                    "$sort": {"timestamp": -1}
                }, 
                {
                    "$match": {"status": 1}
                }, 
                {
                    "$group": {
                        "_id": "$key", 
                        "timestamp": {"$first": "$timestamp"}
                    }
                }
            ]
        )
        last_successes = index_queryset(last_successes, '_id', 'timestamp')
        last_errors = self.collection.aggregate(
            [
                {
                    "$sort": {"timestamp": -1}
                }, 
                {
                    "$match": {"status": {"$ne": 1}}
                }, 
                {
                    "$group": {
                        "_id": "$key", 
                        "timestamp": {"$first": "$timestamp"}
                    }
                }
            ]
        )
        last_errors = index_queryset(last_errors, '_id', 'timestamp')
        last_checks = self.collection.aggregate(
            [
                {
                    "$sort": {"timestamp": -1}
                }, 
                {
                    "$group": {
                        "_id": "$key", 
                        "timestamp": {"$first": "$timestamp"},
                        "status": {"$first": "$status"},
                    }
                }
            ]
        )
        last_checks = index_queryset(last_checks, '_id')
        totals = self.collection.aggregate([{
            "$group": {
                "_id": "$key", 
                "count": {"$sum": 1}
            }
        }])
        totals = index_queryset(totals, '_id', 'count')
        total_success= self.collection.aggregate([
           {
                "$match": {"status": 1}
           }, 
           {
                "$group": {
                    "_id": "$key", 
                    "count": {"$sum": 1}
                }
            }
        ])
        total_success = index_queryset(total_success, '_id', 'count')

        results = {}
        for key in keys:
            last_error = last_errors.get(key, None)
            last_success = last_successes.get(key, None)
            last_check = last_checks.get(key, None)
            if last_check:
                last_check['success'] = last_check['status'] == BaseCheck.STATUS_OK
            results[key] = {
                'last_error': last_error,
                'last_success': last_success,
                'last_check': last_check,
                'total_entry_count': totals.get(key, None),
                'total_success_count': total_success.get(key, None),
            }
        return results
