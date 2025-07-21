
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from . import DOMAIN

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    downloader = hass.data[DOMAIN]["downloader"]
    async_add_entities([YtDlpDownloaderSensor(downloader)])

class YtDlpDownloaderSensor(Entity):
    def __init__(self, downloader):
        self._downloader = downloader
        self._status = self._downloader.status
        self._progress = self._downloader.progress
        self._url = self._downloader.current_url
        self._playlist_status = self._downloader.playlist_status
        self._current_title = self._downloader.current_title

    @property
    def name(self):
        return "YT-DLP Downloader Progress"

    @property
    def state(self):
        return self._progress

    @property
    def unit_of_measurement(self):
        return "%"

    @property
    def extra_state_attributes(self):
        return {
            "status": self._status,
            "playlist_status": self._playlist_status,
            "current_title": self._current_title,
            "url": self._url
        }

    @property
    def should_poll(self):
        return False

    async def async_added_to_hass(self):
        async_dispatcher_connect(self.hass, "yt_dlp_downloader_update", self.async_update_state)

    async def async_update_state(self):
        self._status = self._downloader.status
        self._progress = self._downloader.progress
        self._url = self._downloader.current_url
        self._playlist_status = self._downloader.playlist_status
        self._current_title = self._downloader.current_title
        self.async_write_ha_state()
