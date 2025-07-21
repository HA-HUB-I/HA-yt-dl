
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from .downloader import Downloader
import logging
import asyncio
from homeassistant.helpers import discovery
from homeassistant.helpers.template import Template

DOMAIN = "yt_dlp_downloader"
_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required("download_path"): cv.string,
        vol.Optional("log_level", default="info"): cv.string,
        vol.Optional("write_nfo_files", default=False): cv.boolean,
        vol.Optional("prevent_duplicates", default=True): cv.boolean,
        vol.Optional("sponsorblock_remove", default=[]): cv.ensure_list(cv.string),
    })
}, extra=vol.ALLOW_EXTRA)

def setup(hass: HomeAssistant, config: ConfigType) -> bool:
    conf = config[DOMAIN]
    download_path = conf["download_path"]
    log_level = conf["log_level"]
    write_nfo = conf["write_nfo_files"]
    prevent_duplicates = conf["prevent_duplicates"]
    sponsorblock = conf["sponsorblock_remove"]

    if log_level.lower() == "debug":
        _LOGGER.setLevel(logging.DEBUG)
    else:
        _LOGGER.setLevel(logging.INFO)

    downloader = Downloader(hass, download_path, _LOGGER, write_nfo, prevent_duplicates, sponsorblock)

    hass.data[DOMAIN] = {"downloader": downloader}

    def handle_download(call: ServiceCall) -> None:
        raw_url = call.data.get("url", "")
        raw_format = call.data.get("format", "mp3")

        url = Template(raw_url, hass).render(parse_result=False)
        format = Template(raw_format, hass).render(parse_result=False)

        if not url:
            _LOGGER.error("URL is empty after template rendering. Raw value was: '%s'", raw_url)
            return

        asyncio.run_coroutine_threadsafe(downloader.download_video(url, format), hass.loop)

    hass.services.register(DOMAIN, "download", handle_download)

    discovery.load_platform(hass, "sensor", DOMAIN, {}, config)

    return True

