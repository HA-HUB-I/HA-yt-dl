# YT-DLP Downloader - Home Assistant Integration

Това е персонализирана интеграция за Home Assistant, която ви позволява да сваляте аудио или видео файлове от YouTube и други поддържани сайтове чрез `yt-dlp`.

## Основни Функции

*   **Сваляне на Видео/Аудио**: Поддържа сваляне в MP4 и MP3 формат.
*   **Поддръжка на Плейлисти**: Можете да поставите URL на цял плейлист.
*   **Сензор за Прогрес**: Числов сензор (`sensor.yt_dlp_downloader_progress`), който показва прогреса в проценти и е съвместим с Gauge карти.
*   **Предотвратяване на Дубликати**: Интеграцията помни свалените файлове и ги пропуска, ако се опитате да ги свалите отново.
*   **Интеграция с Jellyfin/Kodi**: Автоматично създава `.nfo` файлове с метаданни.
*   **SponsorBlock**: Автоматично премахва спонсорирани сегменти.

## 1. Инсталация през HACS

1.  В Home Assistant отидете в `HACS` > `Integrations`.
2.  Изберете `Custom repositories` от менюто.
3.  Поставете URL адреса на вашето GitHub хранилище, изберете категория `Integration` и натиснете `Add`.
4.  Намерете новата интеграция в списъка и натиснете `Install`.

## 2. Конфигурация

Добавете следния код във вашия `configuration.yaml` файл:

```yaml
# configuration.yaml

yt_dlp_downloader:
  download_path: /media/videos
  log_level: info
  write_nfo_files: true
  prevent_duplicates: true
  sponsorblock_remove:
    - sponsor
    - selfpromo
```

След като добавите конфигурацията, **рестартирайте Home Assistant**.

## 3. Lovelace Карта

**1. Създайте `input_text` помощник:**
*   Отидете в `Settings` > `Devices & Services` > `Helpers`.
*   Натиснете `Create Helper` и изберете `Text`.
*   Дайте му име, например `YouTube URL Input` (това ще създаде `input_text.youtube_url_input`).

**2. Добавете картата в Lovelace:**

```yaml
type: vertical-stack
cards:
  - type: entities
    entities:
      - entity: input_text.youtube_url_input
        name: YouTube/Playlist URL
  - type: horizontal-stack
    cards:
      - type: button
        name: Свали MP3
        icon: mdi:music
        tap_action:
          action: call-service
          service: yt_dlp_downloader.download
          service_data:
            url: "{{ states('input_text.youtube_url_input') }}"
            format: mp3
      - type: button
        name: Свали MP4
        icon: mdi:movie
        tap_action:
          action: call-service
          service: yt_dlp_downloader.download
          service_data:
            url: "{{ states('input_text.youtube_url_input') }}"
            format: mp4
  - type: conditional
    conditions:
      - entity: sensor.yt_dlp_downloader_progress
        state_not: "0"
    card:
      type: vertical-stack
      cards:
        - type: gauge
          entity: sensor.yt_dlp_downloader_progress
          name: Прогрес на сваляне
          severity:
            green: 75
            yellow: 50
            red: 0
        - type: entities
          entities:
            - entity: sensor.yt_dlp_downloader_progress
              name: Статус
              attribute: status
            - entity: sensor.yt_dlp_downloader_progress
              name: Плейлист
              attribute: playlist_info
              icon: mdi:playlist-music
```
