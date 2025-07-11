
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from .downloader import Downloader
import logging
import asyncio
from homeassistant.helpers import discovery

DOMAIN = "yt_dlp_downloader"
_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required("download_path"): cv.string,
        vol.Optional("log_level", default="info"): cv.string,
    })
}, extra=vol.ALLOW_EXTRA)

def setup(hass: HomeAssistant, config: ConfigType) -> bool:
    conf = config[DOMAIN]
    download_path = conf["download_path"]
    log_level = conf["log_level"]

    if log_level.lower() == "debug":
        _LOGGER.setLevel(logging.DEBUG)
    else:
        _LOGGER.setLevel(logging.INFO)

    downloader = Downloader(hass, download_path, _LOGGER)

    hass.data[DOMAIN] = {"downloader": downloader}

    def handle_download(call: ServiceCall) -> None:
        url = call.data.get("url")
        format = call.data.get("format", "mp3")
        # Use thread-safe method to schedule the coroutine
        asyncio.run_coroutine_threadsafe(downloader.download_video(url, format), hass.loop)

    hass.services.register(DOMAIN, "download", handle_download)

    discovery.load_platform(hass, "sensor", DOMAIN, {}, config)

    return True

