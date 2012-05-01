import requests
import html5lib
import re
import HTMLParser
import datetime

__all__ = ['Noom']

treebuilder = html5lib.treebuilders.getTreeBuilder("dom")
parser = html5lib.HTMLParser(tree=treebuilder)

class Noom(object):

    HOST = 'http://www.noom.com'
    SIGNIN = HOST + '/cardiotrainer/tracks.php'
    TRACKS = HOST + '/cardiotrainer/tracks.php?offset=%s'
    EXPORT = HOST + '/cardiotrainer/exporter/export_gpx.php' \
                  + '?trackId=%s&signature=%s'
    SCRIPT_PATTERN = re.compile(".+= (.*);.*")
    TRACK_ITEM = 'tracklist_item'
    TRACK_CONTENT = 'tracklist_content'
    TRACK_IGNORES = ('totals', 'next')
    DATE_FORMAT = '%A %b.%d, %Y %I:%M %p'

    def __init__(self, user):
        self.session = requests.session()
        access, code = user.split('-')
        self.session.post(Noom.SIGNIN, dict(access=access, code=code))
        self.cache = {}
        self.items = []
        self._iter = self._items()

    def __getitem__(self, item):
        if (isinstance(item, slice)):
            try:
                if item.stop == None:
                    self[-1]
                else:
                    self[item.stop]
            except IndexError:
                pass
            return self.items[item]
        else:
            # reverse index should know lastest item
            if item < 0:
                len(self)
            while len(self.items) <= item:
                try:
                    self._iter.next()
                except StopIteration:
                    raise IndexError("track index out of range")
            return self.items[item]

    def __len__(self):
        try:
            while True:
                self._iter.next()
        except StopIteration:
            return len(self.items)

    def _items(self):
        old_offset = -1
        while True:
            offset = len(self.items)
            if (old_offset == offset):
                raise StopIteration
            old_offset = offset
            for track in self._tracks(offset):
                yield track

    def _tracks(self, offset=0):
        raw = self.session.get(Noom.TRACKS % offset)
        dom = parser.parse(raw.text)
        # <div ... class="tracklist_item ...">...</div>
        get_cls = lambda x: x.getAttribute('class')
        get_id = lambda x: x.getAttribute('id')
        tracks = filter(lambda x: Noom.TRACK_ITEM in get_cls(x) and
                                  get_id(x) not in Noom.TRACK_IGNORES,
                        dom.getElementsByTagName('div'))
        # <script ...>
        script = filter(lambda x: not x.hasAttribute('src') and
                                  'trackData' in x.toxml(),
                        dom.getElementsByTagName('script'))
        if len(script):
            script = script[0].toxml()
            # <script ..> var trackData = {...}; </script>
            s = Noom.SCRIPT_PATTERN.match(script).groups()[0]
            null, true, false = None, True, False
            trackData = eval(HTMLParser.HTMLParser().unescape(s))
        else:
            raise StopIteration
        for track in tracks:
            tid = track.getAttribute('id').replace('track', '')
            item = trackData[tid]
            div = filter(lambda x: Noom.TRACK_CONTENT in get_cls(x), 
                         track.getElementsByTagName('div'))
            date, dist, dur = [''.join(map(lambda x: x.toxml().strip()
                                                      .replace('<br/>', ' '),
                                           x.childNodes)) for x in div]
            try:
                tsign = item['trackIdSignature']
            except KeyError:
                tsign = ''
            item['gpx'] = self.track(tid, tsign)
            item['date'] = datetime.datetime.strptime(date, Noom.DATE_FORMAT)
            item['type'] = item['exercise_type'].replace('exercise_type_', '')
            self.items.append(item)
            yield item

    def track(self, tid, tsign):
        export = Noom.EXPORT % (tid, tsign)
        return self.session.get(export).text

