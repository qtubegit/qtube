from PyQt6 import QtGui
import pathlib

class YtThumbnailCache:
    """
    Global cache for thumbnails. There should be one thumbnail per video ID.
    This should avoid storing the same thumbnail multiple times. Updates to
    a video's thumbnail should affect all tracks with the same video ID. This
    is meant to be a global singleton: notice that the methods and attributes
    are not per instance and use no self attribute.
    """
    thumbnailPath = pathlib.Path(pathlib.Path.home(), '.qtube/thumbnails')
    iconCache = {}

    def iconSize(icon: QtGui.QIcon):
        if icon == None:
            return 0
        size = icon.availableSizes()[-1]
        return size.width() * size.height()

    def updateThumbnail(videoId: str, icon: QtGui.QIcon):
        if icon == None or videoId == None:
            return
        cachedIcon = YtThumbnailCache.getCachedThumbnail(videoId)
        trackSize = YtThumbnailCache.iconSize(icon)
        cachedSize = YtThumbnailCache.iconSize(cachedIcon)
        if trackSize > cachedSize:
            YtThumbnailCache.iconCache[videoId] = icon

    def getCachedThumbnail(videoId: str) -> QtGui.QIcon:
        if videoId == None:
            return None
        if videoId in YtThumbnailCache.iconCache:
            return YtThumbnailCache.iconCache[videoId]

        try:
            iconPath = pathlib.Path(YtThumbnailCache.thumbnailPath, videoId)
            with open(iconPath, 'rb') as fp:
                data = fp.read()
                pixmap = QtGui.QPixmap()
                pixmap.loadFromData(data)
                icon = QtGui.QIcon(pixmap)
                YtThumbnailCache.iconCache[videoId] = icon
                return icon
        except:
            return None