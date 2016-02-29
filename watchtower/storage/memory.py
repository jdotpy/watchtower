from collections import deque
from ..checks import BaseCheck

class MemoryStorage():
    def __init__(self, max_history=40):
        self.max_history = max_history
        self.results = {}

    def _init_for_key(self, key):
        self.results[key] = {
            'history': deque(maxlen=self.max_history),
            'last_error': None,
            'last_success': None,
            'total_entry_count': 0,
            'total_success_count': 0
        }

    def log_result(self, key, timestamp, status):
        event = {'status': status, 'timestamp': timestamp}
        if key not in self.results:
            self._init_for_key(key)
        key_results = self.results.get(key)

        success = status == BaseCheck.STATUS_OK
        key_results['history'].append(event)
        key_results['total_entry_count'] += 1
        if success:
            key_results['last_success'] = event
            key_results['total_success_count'] += 1
        else:
            key_results['last_error'] = event 

    def summary(self, keys):
        results = {}
        for key in keys:
            results[key] = self.summary(key)
        self.results.get(key)
        return results
