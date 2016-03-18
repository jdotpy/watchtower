import requests

class BaseAlert():
    DEFAULT_ACK_TEXT = 'We are working to resolve the issue'
    MIN_STATUS = 2
    
    def __init__(self, name, options, issue_options):
        self.name = name
        self.options = options
        
        self.trigger_issue = issue_options.get('trigger_issue', False)
        self.issue_auto_ack = issue_options.get('issue_auto_ack', False)
        self.issue_auto_ack_text = issue_options.get('issue_auto_ack_text', self.DEFAULT_ACK_TEXT)

    def trigger(self, check, status):
        print('Triggering Alert [{}]: {}'.format(
            self.__class__.__name__,
            self.name
        ))
        self.alert(check, status)

    def alert(self, check, status):
        pass

class Webhook(BaseAlert):
    def alert(self, check, status):
        url = self.options.get('url')
        try:
            response = requests.get(url, verify=False)
        except Exception as e:
            pass

class SimpleSMTP(BaseAlert):
    pass
