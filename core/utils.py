import uuid
import hashlib
import datetime

class Utils:
    @classmethod
    def uuid(cls):
        return str(uuid.uuid4())
    
    @classmethod
    def get_local_date(cls):
        return datetime.datetime.now().strftime("%d/%m/%Y")

    @classmethod
    def gethash(cls, data):
        hash_obj = hashlib.md5(data.encode())
        return hash_obj.hexdigest()
    
