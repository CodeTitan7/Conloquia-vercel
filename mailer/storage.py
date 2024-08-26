import os
from supabase import create_client, Client
from django.core.files.storage import Storage
from django.core.files.base import ContentFile

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

class SupabaseStorage(Storage):
    def __init__(self):
        self.client = create_client(
            SUPABASE_URL,
            SUPABASE_KEY
        )
        self.bucket = 'user-profile-pictures'

    def _open(self, name, mode='rb'):
        try:
            response = self.client.storage.from_(self.bucket).download(name)
            return ContentFile(response.content, name)
        except Exception as e:
            raise FileNotFoundError(f"Could not open file: {e}")

    def _save(self, name, content):
        try:
            file_data = content.read()
            self.client.storage.from_(self.bucket).upload(name, file_data)
            return name
        except Exception as e:
            raise Exception(f"Could not save file: {e}")

    def url(self, name):
        try:
            return self.client.storage.from_(self.bucket).get_public_url(name)
        except Exception as e:
            raise Exception(f"Could not retrieve file URL: {e}")

    def exists(self, name):
        try:
            response = self.client.storage.from_(self.bucket).download(name)
            return response.status_code == 200
        except:
            return False

    def delete(self, name):
        try:
            self.client.storage.from_(self.bucket).remove([name])
        except Exception as e:
            raise Exception(f"Could not delete file: {e}")

    def generate_signed_url(self, file_name, expires_in=3600):
        try:
            response = self.client.storage.from_(self.bucket).create_signed_url(file_name, expires_in)
            return response['signedURL']
        except Exception as e:
            raise Exception(f"Could not generate signed URL: {e}")