"""
davclient
Module to load data into data structures from the "attr" module
"""

# Copyright (C) 2019 Salvo "LtWorf" Tomaselli
#
# davclient is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# author Salvo "LtWorf" Tomaselli <tiposchi@tiscali.it>

from base64 import b64encode
from urllib3 import HTTPSConnectionPool, HTTPConnectionPool
import urllib
import stat
from typing import Dict, Iterable, NamedTuple, Optional, Union
import xml.etree.ElementTree as ET


class Props(NamedTuple):
    st_mode: int
    st_size: int
    st_nlink: int
    st_ctime: float
    st_mtime: float
    st_atime: float


class DavClient:
    def __init__(self, url: str, username: Optional[bytes], password: Optional[bytes]) -> None:

        url_data = urllib.parse.urlsplit(url)

        if url_data.scheme in {'http', 'webdav'}:
            ConnectionPool = HTTPConnectionPool
        else:
            ConnectionPool = HTTPSConnectionPool

        self.base_href = url_data.path

        if url_data.query or url_data.fragment:
            raise Exception('Invalid connection query')

        self.pool = ConnectionPool(url_data.netloc, maxsize=1)

        self.default_headers: Dict[str, Union[bytes, str]] = {}
        if username is not None:
            self.default_headers['Authorization'] = b64encode(b'Basic {username}:{password}')

    def _fixhref(self, href: str) -> str:
        return urllib.parse.quote(self.base_href + href)

    def stat(self, href: str) -> Props:
        href = self._fixhref(href)
        headers = {}
        headers.update(self.default_headers)
        r = self.pool.request('PROPFIND', href, headers=headers)
        if r.status != 207:
            raise Exception('Invalid status')
        root = ET.fromstring(r.data)

        size = root[0].find('{DAV:}propstat').find('{DAV:}prop').find('{DAV:}getcontentlength').text
        m_time = root[0].find('{DAV:}propstat').find('{DAV:}prop').find('{DAV:}getlastmodified').text

        if len(root[0].find('{DAV:}propstat').find('{DAV:}prop').find('{DAV:}resourcetype')):
            # The OR is to give it EXEC permissions
            st_mode = stat.S_IFDIR | 0o500
        else:
            st_mode = stat.S_IFREG | 0o400

        return Props(
            st_mode=st_mode,
            st_size=int(size),
            st_nlink=1, #FIXME
            st_ctime=0, #FIXME
            st_mtime=0, #FIXME
            st_atime=0, #FIXME
        )

    def list_files(self, href: str) -> Iterable[str]:
        href = self._fixhref(href)
        headers = {'Depth': '1'}
        headers.update(self.default_headers)
        r = self.pool.request('PROPFIND', href, headers=headers)
        if r.status != 207:
            raise Exception('Invalid status')

        root = ET.fromstring(r.data)
        for i in root:
            partial = i.find('{DAV:}href').text
            partial = urllib.parse.unquote(partial)
            partial = partial.split('/')[-1]
            if partial:
                yield partial

    def read(self, href: str, start: int, end: int) -> bytes:
        props = self.stat(href)
        href = self._fixhref(href)

        headers = {}
        if end < props.st_size:
            headers['Range'] = f'bytes={start}-{end - 1}'
        else:
            headers['Range'] = f'bytes={start}-{props.st_size - 1}'

        headers.update(self.default_headers)

        r = self.pool.request('GET', href, headers=headers)
        if r.status != 206:
            raise Exception(f'Invalid status: {r.status}')
        return r.data
