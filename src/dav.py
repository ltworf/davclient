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

from urllib3 import HTTPSConnectionPool
from typing import Iterable
import xml.etree.ElementTree as ET


class DavClient:
    def __init__(self, hostname: str) -> None:
        self.pool = HTTPSConnectionPool(hostname, maxsize=1)

    def list_files(self, href: str) -> Iterable[str]:
        headers = {'Depth': '1'}
        r = self.pool.request('PROPFIND', href, headers=headers)
        if r.status != 207:
            raise Exception('Invalid status')

        root = ET.fromstring(r.data)

        hreflen = len(href)
        for i in root:
             partial = i.find('{DAV:}href').text[hreflen:]
             if partial:
                 yield partial
