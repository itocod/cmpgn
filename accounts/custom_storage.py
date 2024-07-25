from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from urllib.request import urlopen
from urllib.parse import urljoin
from django.conf import settings

class GitHubStorage(Storage):
    def __init__(self, base_url=None):
        if not base_url:
            base_url = settings.GITHUB_BASE_URL
        self.base_url = base_url

    def _open(self, name, mode='rb'):
        url = urljoin(self.base_url, name)
        content = urlopen(url).read()
        return ContentFile(content)

    def _save(self, name, content):
        raise NotImplementedError("This backend is read-only")

    def url(self, name):
        return urljoin(self.base_url, name)

    def exists(self, name):
        try:
            urlopen(urljoin(self.base_url, name))
            return True
        except:
            return False
