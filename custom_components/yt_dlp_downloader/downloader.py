import yt_dlp
import asyncio
import os
import xml.etree.ElementTree as ET
from homeassistant.helpers.dispatcher import async_dispatcher_send

class Downloader:
    def __init__(self, hass, download_path, logger, write_nfo, prevent_duplicates, sponsorblock):
        self.hass = hass
        self.download_path = download_path
        self._logger = logger
        self._write_nfo = write_nfo
        self._prevent_duplicates = prevent_duplicates
        self._sponsorblock = sponsorblock

        self.current_url = None
        self.progress = 0
        self.status = "idle"
        self.playlist_info = ""

        # Path for the archive file to prevent duplicates
        self.archive_file = os.path.join(self.hass.config.config_dir, ".yt-dlp-archive.txt")

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            self.status = "Downloading"
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            if total_bytes:
                downloaded_bytes = d.get('downloaded_bytes')
                self.progress = (downloaded_bytes / total_bytes) * 100
            
            # Update playlist info if available
            playlist_index = d.get('playlist_index')
            playlist_count = d.get('playlist_count')
            if playlist_index and playlist_count:
                self.playlist_info = f"(Video {playlist_index}/{playlist_count})"
            else:
                self.playlist_info = ""

            self.update_sensor()

        if d['status'] == 'finished':
            self.status = "Finished"
            self.progress = 100
            self.update_sensor()

            if self._write_nfo:
                self.create_nfo_file(d['info_dict'])

            # Reset after a short delay
            asyncio.run_coroutine_threadsafe(self.reset_status(), self.hass.loop)

    def create_nfo_file(self, info):
        media_type = 'movie' if info.get('duration', 0) > 300 else 'musicvideo' # Simple logic: >5min is a movie
        root = ET.Element(media_type)

        ET.SubElement(root, "title").text = info.get('title')
        ET.SubElement(root, "plot").text = info.get('description')
        ET.SubElement(root, "year").text = str(info.get('upload_date', '')[:4])
        ET.SubElement(root, "id").text = info.get('id')
        ET.SubElement(root, "tagline").text = f"Uploaded by {info.get('uploader')}"
        ET.SubElement(root, "channel").text = info.get('channel')

        # Add tags
        tags = info.get('tags', [])
        if tags:
            for tag in tags:
                ET.SubElement(root, "tag").text = tag

        # Write to file
        base_filepath = os.path.splitext(info['_filename'])[0]
        nfo_filepath = f"{base_filepath}.nfo"
        try:
            tree = ET.ElementTree(root)
            tree.write(nfo_filepath, encoding='utf-8', xml_declaration=True)
            self._logger.debug(f"Successfully created NFO file: {nfo_filepath}")
        except Exception as e:
            self._logger.error(f"Failed to write NFO file {nfo_filepath}: {e}")

    async def reset_status(self):
        await asyncio.sleep(10) # Increased delay to ensure all operations are finished
        self.status = "idle"
        self.progress = 0
        self.current_url = None
        self.playlist_info = ""
        self.update_sensor()

    def update_sensor(self):
        self.hass.loop.call_soon_threadsafe(
            async_dispatcher_send, self.hass, "yt_dlp_downloader_update"
        )

    async def download_video(self, url, format):
        self.current_url = url
        self.status = "Starting"
        self.progress = 0
        self.update_sensor()

        ydl_opts = {
            'format': 'bestaudio/best' if format == 'mp3' else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }] if format == 'mp3' else [],
            'progress_hooks': [self.progress_hook],
            'logger': self._logger,
            'writemetadata': True, # Needed for some metadata
            'writeinfojson': self._write_nfo, # Download info json only if we need it for NFO
        }

        if self._prevent_duplicates:
            ydl_opts['download_archive'] = self.archive_file

        if self._sponsorblock:
            ydl_opts['postprocessors'] = ydl_opts.get('postprocessors', []) + [{
                'key': 'SponsorBlock',
                'categories': self._sponsorblock
            }, {
                'key': 'ModifyChapters',
                'remove_sponsor_segments': self._sponsorblock
            }]

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                await self.hass.async_add_executor_job(ydl.download, [url])
        except Exception as e:
            self._logger.error(f"Error downloading {url}: {e}")
            self.status = "Error"
            self.update_sensor()
            await self.reset_status()

