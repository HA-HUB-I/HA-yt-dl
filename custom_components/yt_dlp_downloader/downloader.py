import yt_dlp
import asyncio
from homeassistant.helpers.dispatcher import async_dispatcher_send

class Downloader:
    def __init__(self, hass, download_path, logger):
        self.hass = hass
        self.download_path = download_path
        self._logger = logger
        self.current_url = None
        self.progress = 0
        self.status = "idle"

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            self.status = "Downloading"
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            if total_bytes:
                downloaded_bytes = d.get('downloaded_bytes')
                self.progress = (downloaded_bytes / total_bytes) * 100
            self.update_sensor()

        if d['status'] == 'finished':
            self.status = "Finished"
            self.progress = 100
            self.update_sensor()
            # Reset after a short delay
            asyncio.run_coroutine_threadsafe(self.reset_status(), self.hass.loop)

    async def reset_status(self):
        await asyncio.sleep(5)
        self.status = "idle"
        self.progress = 0
        self.current_url = None
        self.update_sensor()

    def update_sensor(self):
        """Schedule sensor update in the event loop."""
        self.hass.loop.call_soon_threadsafe(
            async_dispatcher_send, self.hass, "yt_dlp_downloader_update"
        )

    async def download_video(self, url, format):
        self.current_url = url
        self.status = "Starting"
        self.progress = 0
        self.update_sensor()

        ydl_opts = {
            'format': 'bestaudio/best' if format == 'mp3' else 'best',
            'outtmpl': f"{self.download_path}/%(title)s.%(ext)s",
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }] if format == 'mp3' else [],
            'progress_hooks': [self.progress_hook],
            'logger': self._logger,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                await self.hass.async_add_executor_job(ydl.download, [url])
        except Exception as e:
            self._logger.error(f"Error downloading {url}: {e}")
            self.status = "Error"
            self.update_sensor()
            await self.reset_status()

