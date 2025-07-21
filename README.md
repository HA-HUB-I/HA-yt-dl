# YT-DLP Downloader - Home Assistant Integration

Това е персонализирана интеграция за Home Assistant, която ви позволява да сваляте аудио или видео файлове от YouTube и други поддържани сайтове чрез `yt-dlp`.

## Основни Функции

*   **Сваляне на Видео/Аудио/Плейлисти**.
*   **Контрол на Свалянето**: Бутон за прекратяване на текущото сваляне.
*   **Детайлен Сензор за Прогрес**: Показва общ прогрес, име на текущия файл и брояч за плейлисти (напр. 5/21).
*   **Вграждане на Метаданни**: Автоматично вгражда изпълнител, заглавие, албум и обложка в MP3 файловете.
*   **Интеграция с Jellyfin/Kodi**: Автоматично създава `.nfo` файлове.
*   **SponsorBlock**: Автоматично премахва спонсорирани сегменти.
*   **Предотвратяване на Дубликати**.

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
  download_path: /media/music
  log_level: info

  # --- Метаданни за Jellyfin/MP3 ---
  write_nfo_files: true
  embed_metadata: true
  embed_thumbnail: true
  # Позволява извличане на метаданни от заглавието. Пример: "Artist - Title"
  parse_metadata_from_title: '%(artist)s - %(title)s'

  # --- Контрол на свалянето ---
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
*   Дайте му име, например `YouTube URL Input`.

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
        name: Свали MP3 (Плейлист)
        icon: mdi:playlist-music
        tap_action:
          action: call-service
          service: yt_dlp_downloader.download
          service_data:
            url: "{{ states('input_text.youtube_url_input') }}"
            format: mp3
            playlist_items: all
      - type: button
        name: Свали MP3 (Първата)
        icon: mdi:music
        tap_action:
          action: call-service
          service: yt_dlp_downloader.download
          service_data:
            url: "{{ states('input_text.youtube_url_input') }}"
            format: mp3
            playlist_items: first
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
        - type: entities
          entities:
            - entity: sensor.yt_dlp_downloader_progress
              name: Статус
              attribute: status
            - entity: sensor.yt_dlp_downloader_progress
              name: Файл
              attribute: current_title
            - entity: sensor.yt_dlp_downloader_progress
              name: Плейлист
              attribute: playlist_status
        - type: button
          name: Прекрати
          icon: mdi:cancel
          action: call-service
          service: yt_dlp_downloader.cancel
```