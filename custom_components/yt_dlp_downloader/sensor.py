
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
        self._playlist_info = self._downloader.playlist_info

    @property
    def name(self):
        return "YT-DLP Downloader Progress"

    @property
    def state(self):
        """Return the state of the sensor (the progress)."""
        return self._progress

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return "%"

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "status": self._status,
            "playlist_info": self._playlist_info,
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
        self._playlist_info = self._downloader.playlist_info
        self.async_write_ha_state()
