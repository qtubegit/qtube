from YtTrack import YtTrack

class YtPlaylist:
    def __init__(self, name: str, tracks: list=None):
        self.name = name
        if tracks == None:
            self.tracks = []
        else:
            self.tracks = tracks
    
    def __repr__(self) -> str:
        s = '\n'.join(f'{repr(t)}' for t in self.tracks)
        if len(self.tracks) == 0:
            s = '<Empty>'
        return f'\n\n{self.name}:\n{s}'

    def __eq__(self, other) -> bool:
        if other == None:
            return False
        return self.name == other.name

    def __getitem__(self, key: int) -> YtTrack:
        return self.tracks[key % len(self.tracks)]

    def __iter__(self):
        return iter(self.tracks)

    def __delitem__(self, track: YtTrack):
        if track not in self.tracks:
            return
        index = self.tracks.index(track)
        del(self.tracks[index])

    def __len__(self):
        return len(self.tracks)