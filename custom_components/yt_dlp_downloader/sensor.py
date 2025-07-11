
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from . import DOMAIN

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    downloader = hass.data[DOMAIN]["downloader"]
    async_add_entities([YtDlpDownloaderSensor(downloader)])

class YtDlpDownloaderSensor(Entity):
    def __init__(self, downloader):
        self._downloader = downloader
        self._state = self._downloader.status
        self._progress = self._downloader.progress
        self._url = self._downloader.current_url

    @property
    def name(self):
        return "YT-DLP Downloader Status"

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return {
            "progress": self._progress,
            "url": self._url
        }

    @property
    def should_poll(self):
        return False

    async def async_added_to_hass(self):
        async_dispatcher_connect(self.hass, "yt_dlp_downloader_update", self.async_update_state)

    async def async_update_state(self):
        self._state = self._downloader.status
        self._progress = self._downloader.progress
        self._url = self._downloader.current_url
        self.async_write_ha_state()
