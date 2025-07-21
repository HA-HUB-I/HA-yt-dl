import yt_dlp
import asyncio
import os
import xml.etree.ElementTree as ET
from homeassistant.helpers.dispatcher import async_dispatcher_send
import threading

class Downloader:
    def __init__(self, hass, download_path, logger, prevent_duplicates, write_nfo, embed_metadata, embed_thumbnail, parse_metadata, sponsorblock):
        self.hass = hass
        self.download_path = download_path
        self._logger = logger
        self._prevent_duplicates = prevent_duplicates
        self._write_nfo = write_nfo
        self._embed_metadata = embed_metadata
        self._embed_thumbnail = embed_thumbnail
        self._parse_metadata = parse_metadata
        self._sponsorblock = sponsorblock

        # State properties
        self.status = "idle"
        self.progress = 0
        self.current_title = None
        self.playlist_status = None
        self.current_url = None

        self.archive_file = os.path.join(self.hass.config.config_dir, ".yt-dlp-archive.txt")
        self._cancel_event = threading.Event()

    def cancel_download(self):
        self._logger.info("Download cancellation requested.")
        self._cancel_event.set()

    def progress_hook(self, d):
        if self._cancel_event.is_set():
            raise yt_dlp.utils.DownloadCancelled("Download cancelled by user.")

        if d['status'] == 'downloading':
            self.status = "Downloading"
            self.current_title = d.get('filename')
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            if total_bytes:
                self.progress = (d.get('downloaded_bytes') / total_bytes) * 100

            playlist_index = d.get('playlist_index')
            playlist_count = d.get('playlist_count')
            if playlist_index and playlist_count:
                self.playlist_status = f"{playlist_index}/{playlist_count}"
            
            self.update_sensor()

        elif d['status'] == 'finished':
            self.status = "Processing"
            self.update_sensor()
            if self._write_nfo:
                self.create_nfo_file(d['info_dict'])

    def create_nfo_file(self, info):
        # ... (NFO logic remains the same)
        pass

    async def reset_status(self):
        await asyncio.sleep(10)
        self.status = "idle"
        self.progress = 0
        self.current_title = None
        self.playlist_status = None
        self.current_url = None
        self.update_sensor()

    def update_sensor(self):
        self.hass.loop.call_soon_threadsafe(
            async_dispatcher_send, self.hass, "yt_dlp_downloader_update"
        )

    async def download_video(self, url, format, playlist_items):
        self._cancel_event.clear()
        self.current_url = url
        self.status = "Starting"
        self.update_sensor()

        ydl_opts = {
            'format': 'bestaudio/best' if format == 'mp3' else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
            'progress_hooks': [self.progress_hook],
            'logger': self._logger,
            'writemetadata': self._write_nfo or self._embed_metadata,
            'writeinfojson': self._write_nfo,
        }

        if playlist_items == 'first':
            ydl_opts['playlist_items'] = '1'

        if self._prevent_duplicates:
            ydl_opts['download_archive'] = self.archive_file

        postprocessors = []
        if format == 'mp3':
            postprocessors.append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            })

        if self._embed_metadata:
            postprocessors.append({'key': 'FFmpegMetadata'})
        
        if self._embed_thumbnail:
            postprocessors.append({'key': 'EmbedThumbnail'})

        if self._parse_metadata:
            postprocessors.append({
                'key': 'MetadataFromTitle',
                'titleformat': self._parse_metadata
            })

        if self._sponsorblock:
            postprocessors.extend([{
                'key': 'SponsorBlock',
                'categories': self._sponsorblock
            }, {
                'key': 'ModifyChapters',
                'remove_sponsor_segments': self._sponsorblock
            }])

        if postprocessors:
            ydl_opts['postprocessors'] = postprocessors

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                await self.hass.async_add_executor_job(ydl.download, [url])
            self.status = "Finished"
        except yt_dlp.utils.DownloadCancelled:
            self.status = "Cancelled"
            self._logger.info("Download was successfully cancelled.")
        except Exception as e:
            self.status = "Error"
            self._logger.error(f"Error downloading {url}: {e}")
        finally:
            self.progress = 0
            self.update_sensor()
            await self.reset_status()

