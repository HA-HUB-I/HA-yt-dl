
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
        vol.Optional("prevent_duplicates", default=True): cv.boolean,
        # Metadata options
        vol.Optional("write_nfo_files", default=False): cv.boolean,
        vol.Optional("embed_metadata", default=True): cv.boolean,
        vol.Optional("embed_thumbnail", default=True): cv.boolean,
        vol.Optional("parse_metadata_from_title", default=""): cv.string,
        # SponsorBlock options
        vol.Optional("sponsorblock_remove", default=[]): cv.ensure_list(cv.string),
    })
}, extra=vol.ALLOW_EXTRA)

def setup(hass: HomeAssistant, config: ConfigType) -> bool:
    conf = config[DOMAIN]

    downloader = Downloader(
        hass,
        conf["download_path"],
        _LOGGER,
        conf["prevent_duplicates"],
        conf["write_nfo_files"],
        conf["embed_metadata"],
        conf["embed_thumbnail"],
        conf["parse_metadata_from_title"],
        conf["sponsorblock_remove"],
    )

    hass.data[DOMAIN] = {"downloader": downloader}

    def handle_download(call: ServiceCall) -> None:
        raw_url = call.data.get("url", "")
        raw_format = call.data.get("format", "mp3")
        playlist_items = call.data.get("playlist_items", "all")

        url = Template(raw_url, hass).render(parse_result=False)
        format = Template(raw_format, hass).render(parse_result=False)

        if not url:
            _LOGGER.error("URL is empty after template rendering. Raw value was: '%s'", raw_url)
            return

        asyncio.run_coroutine_threadsafe(downloader.download_video(url, format, playlist_items), hass.loop)

    def handle_cancel(call: ServiceCall) -> None:
        downloader.cancel_download()

    hass.services.register(DOMAIN, "download", handle_download)
    hass.services.register(DOMAIN, "cancel", handle_cancel)

    discovery.load_platform(hass, "sensor", DOMAIN, {}, config)

    return True

