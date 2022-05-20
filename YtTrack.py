from YtThumbnailCache import YtThumbnailCache

class YtTrack:
    @property
    def icon(self):
        return YtThumbnailCache.getCachedThumbnail(self.videoId)

    def __init__(self, title: str, playlist = None, **tags):
        """ 
        There is a variety of information that could be available for any given track,
        such as Last.fm information, YouTube ID, album, artist, release date, artwork,
        position the user left off playing, and many more. Instead of trying to constrain
        or anticipate all possible future attributes, keep anything optional in a dictionary
        indexed by tags as keys. Those tags represent a given such attribute.

        Everything in those tags will be serialized when saving a playlist and deserialized 
        when loading a playlist. There can also be properties that are associated with a track
        but should not be saved, such as thumbnails. Those will be derived from the videoId or
        possibly other attributes in the future. This should be flexible enough to possibly 
        support other services in the future, such as SoundCloud.
        """
        # These will be regular object attributes.
        self.playlist = playlist
        self._tags = tags

        # All other attributes to go into tags.
        self._setattr_pre_init = self._setattr_post_init
        self.title = title

        if self.position == None:
            self.position = 0

        if self.playTime == None:
            self.playTime = 0

    def _setattr_post_init(self, k, v):
        # The attribute is regular class attribute, not a 
        # tag, so retrieve it as usual. 
        if k in self.__dict__:
            super().__setattr__(k, v)
            return
        # Otherwise, assign to  a tag. This will be true 
        # for all member assignments after construction.
        self._tags[k] = v

    def _setattr_pre_init(self, k, v):
        super().__setattr__(k, v)

    def __setattr__(self, k, v):
        self._setattr_pre_init(k, v)

    def __getattr__(self, a):
        if a in self._tags:
            return self._tags[a]
        return None

    def __repr__(self) -> str:
        return f'Track: {self._tags}'

    def getTags(self) -> dict:
        return self._tags

    def makeCopy(self):
        tags = { t: self._tags[t] for t in self._tags if t != 'title' }
        track = YtTrack(self.title, **tags)

        # Copies having their play position and play time reset seems nicer.
        # It also provides the currently only way to reset play time.
        track.position = 0
        track.playTime = 0
        
        return track