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

    def __getitem__(self, index: int) -> YtTrack:
        if len(self.tracks) == 0:
            return None
        return self.tracks[index % len(self.tracks)]

    def __iter__(self):
        return iter(self.tracks)

    def __delitem__(self, track: YtTrack):
        if track not in self.tracks:
            return
        index = self.tracks.index(track)
        del(self.tracks[index])

    def __len__(self):
        return len(self.tracks)
    
    def trackIndex(self, track: YtTrack) -> int:
        try:
            return self.tracks.index(track)
        except ValueError:
            return -1
