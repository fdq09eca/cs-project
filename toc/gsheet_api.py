from googleapiclient.discovery import build
class GSheet:
    SCOPES = ''
    
    def __init__(self, creds_path):
        self.creds = creds_path
    
    @property
    def creds(self):
        return self._creds
    
    @creds.setter
    def creds(self, creds_json='credentials.json'):
        
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self._creds = pickle.load(token)
        
        if not self._creds or not self._creds.valid:
            if self._creds and self._creds.expired and self._creds.refresh_token:
                self._creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(creds_json, SCOPES)
                self._creds = flow.run_local_server(port=0)
        return self._creds
    
    @create_sheet('')
    
