from hashlib import sha1
from io import StringIO
from os.path import basename
from pcloud.validate import RequiredParameterCheck

import argparse
import logging
import requests


log = logging.getLogger('pycloud')


# File open flags https://docs.pcloud.com/methods/fileops/file_open.html
O_WRITE = int('0x0002', 16)
O_CREAT = int('0x0040', 16)
O_EXCL = int('0x0080', 16)
O_TRUNC = int('0x0200', 16)
O_APPEND = int('0x0400', 16)


# Exceptions
class AuthenticationError(Exception):
    """ Authentication failed """


def main():
    parser = argparse.ArgumentParser(description='pCloud command line client')
    parser.add_argument('username',
                    help='The username for login into your pCloud account')
    parser.add_argument('password',
                    help='The password for login into your pCloud account')
    args = parser.parse_args()
    pyc = PyCloud(args.username, args.password)


class PyCloud(object):

    endpoint = 'https://api.pcloud.com/'

    def __init__(self, username, password):
        self.username = username.lower().encode('utf-8')
        self.password = password.encode('utf-8')
        self.session = requests.Session()
        self.auth_token = self.get_auth_token()

    def _do_request(self, method, authenticate=True, json=True, **kw):
        if authenticate:
             params = {'auth': self.auth_token}
        else:
             params = {}
        params.update(kw)
        log.debug('Doing request to %s%s', self.endpoint, method)
        log.debug('Params: %s', params)
        resp = self.session.get(self.endpoint + method, params=params)
        if json:
            return resp.json()
        else:
            return resp.content

    # Authentication
    def getdigest(self):
        resp = self._do_request('getdigest', authenticate=False)
        return bytes(resp['digest'], 'utf-8')

    def get_auth_token(self):
        digest = self.getdigest()
        passworddigest = sha1(
            self.password +
            bytes(sha1(self.username).hexdigest(), 'utf-8') +
            digest)
        params={'getauth': 1,
            'logout': 1,
            'username': self.username.decode('utf-8'),
            'digest': digest.decode('utf-8'),
            'passworddigest': passworddigest.hexdigest()}
        resp = self._do_request('userinfo', authenticate=False, **params)
        if 'auth' not in resp:
            print(resp)
            raise(AuthenticationError)
        return resp['auth']

    # Folders
    @RequiredParameterCheck(('path', 'folderid'))
    def createfolder(self, **kwargs):
        return self._do_request('createfolder', **kwargs)

    @RequiredParameterCheck(('path', 'folderid'))
    def listfolder(self, **kwargs):
        return self._do_request('listfolder', **kwargs)

    @RequiredParameterCheck(('path', 'folderid'))
    def renamefolder(self, **kwargs):
        return self._do_request('renamefolder', **kwargs)

    @RequiredParameterCheck(('path', 'folderid'))
    def deletefolder(self, **kwargs):
        return self._do_request('deletefolder', **kwargs)

    @RequiredParameterCheck(('path', 'folderid'))
    def deletefolderrecursive(self, **kwargs):
        return self._do_request('deletefolderrecursive', **kwargs)

    # File
    @RequiredParameterCheck(('files', 'data'))
    def uploadfile(self, **kwargs):
        kwargs['auth'] = self.auth_token
        if 'files' in kwargs:
            for f in kwargs['files']:
                filename = basename(f)
                files = {filename: open(f, 'rb')}
                kwargs['filename'] = filename
        else:  # 'data' in kwargs:
            filename = kwargs['filename']
            files = {filename: StringIO(kwargs['data'])}
        resp = requests.post(
            self.endpoint + 'uploadfile',
            files=files,
            data=kwargs)
        return resp.json()

    @RequiredParameterCheck(('progresshash',))
    def uploadprogress(self, **kwargs):
        return self._do_request('uploadprogress', **kwargs)

    @RequiredParameterCheck(('links',))
    def downloadfile(self, **kwargs):
        return self._do_request('downloadfile', **kwargs)

    def copyfile(self, **kwargs):
        pass

    @RequiredParameterCheck(('path', 'fileid'))
    def checksumfile(self, **kwargs):
        return self._do_request('checksumfile', **kwargs)

    @RequiredParameterCheck(('path', 'fileid'))
    def deletefile(self, **kwargs):
        return self._do_request('deletefile', **kwargs)

    def renamefile(self, **kwargs):
        return self._do_request('renamefile', **kwargs)

    # Auth
    def sendverificationemail(self, **kwargs):
        return self._do_request('sendverificationemail', **kwargs)

    def verifyemail(self, **kwargs):
        return self._do_request('verifyemail', **kwargs)

    def changepassword(self, **kwargs):
        return self._do_request('changepassword', **kwargs)

    def lostpassword(self, **kwargs):
        return self._do_request('lostpassword', **kwargs)

    def resetpassword(self, **kwargs):
        return self._do_request('resetpassword', **kwargs)

    def register(self, **kwargs):
        return self._do_request('register', **kwargs)

    def invite(self, **kwargs):
        return self._do_request('invite', **kwargs)

    def userinvites(self, **kwargs):
        return self._do_request('userinvites', **kwargs)

    def logout(self, **kwargs):
        return self._do_request('logout', **kwargs)

    def listtokens(self, **kwargs):
        return self._do_request('listtokens', **kwargs)

    def deletetoken(self, **kwargs):
        return self._do_request('deletetoken', **kwargs)

    #file
    @RequiredParameterCheck(('flags',))
    def file_open(self, **kwargs):
        return self._do_request('file_open', **kwargs)

    @RequiredParameterCheck(('fd',))
    def file_read(self, **kwargs):
        return self._do_request('file_read', json=False, **kwargs)


if __name__ == '__main__':
    main()