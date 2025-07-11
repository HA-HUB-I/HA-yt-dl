
# YT-DLP Downloader - Home Assistant Integration

Това е персонализирана интеграция за Home Assistant, която ви позволява да сваляте аудио или видео файлове от YouTube и други поддържани сайтове чрез `yt-dlp`.

## Нови Функции

*   **Сензор за статус**: Интеграцията вече предоставя сензор (`sensor.yt_dlp_downloader_status`), който показва текущото състояние на свалянето (`idle`, `Downloading`, `Finished`, `Error`).
*   **Прогрес**: Сензорът има атрибут `progress`, който показва прогреса на сваляне в проценти.
*   **Контрол на логирането**: Можете да настроите нивото на логиране в конфигурацията.

## 1. Качване в GitHub

За да използвате тази интеграция с HACS, първо трябва да я качите във вашето собствено GitHub хранилище.

1.  Създайте ново **публично** хранилище (repository) във вашия GitHub акаунт.
2.  Качете всички файлове от този проект (`custom_components` директорията, `hacs.json` и този `README.md`) във вашето ново хранилище.
3.  **Важно**: Отворете файла `custom_components/yt_dlp_downloader/manifest.json` и променете `"@youruser"` с вашето потребителско име в GitHub.

## 2. Инсталация през HACS

След като хранилището е създадено в GitHub, следвайте тези стъпки в Home Assistant:

1.  Отидете в `HACS` > `Integrations`.
2.  Натиснете бутона с трите точки в горния десен ъгъл и изберете `Custom repositories`.
3.  В полето `Repository` поставете URL адреса на вашето GitHub хранилище.
4.  В полето `Category` изберете `Integration`.
5.  Натиснете `Add`.
6.  Вашата нова интеграция ще се появи в списъка. Натиснете върху нея и след това `Install`.

## 3. Конфигурация

След инсталацията е необходимо да конфигурирате интеграцията, като добавите следния код във вашия `configuration.yaml` файл:

```yaml
# configuration.yaml

yt_dlp_downloader:
  download_path: /media
  log_level: debug # по избор, може да бъде 'info' или 'debug'
```

*   `download_path`: Директорията, в която ще се запазват файловете (препоръчително `/media`).
*   `log_level`: Ако е `debug`, в логовете на Home Assistant ще се записва пълна информация от `yt-dlp`, което е полезно при проблеми.

След като добавите конфигурацията, **рестартирайте Home Assistant**.

## 4. Тестване и Lovelace Карта

Можете да тествате услугата от `Developer Tools` > `Services`, както е описано в предишната версия.

### Lovelace Карта

Можете да създадете и карта в Lovelace за по-лесно управление. Ето един пример, който използва `input_text` за URL, бутони за избор на формат и показва статуса на сваляне.

**1. Създайте `input_text` помощник (helper):**

Първо, трябва да създадете поле за въвеждане на текст, където ще поставяте URL адресите.

*   Отидете в `Settings` > `Devices & Services` > `Helpers`.
*   Натиснете бутона `Create Helper` и изберете `Text` от списъка.
*   В полето `Name` въведете име, например `YouTube URL Input`. Това име автоматично ще създаде ID-то, което ни трябва: `input_text.youtube_url_input`.
*   Можете да добавите и икона, например `mdi:youtube`.
*   Натиснете `Create`.

**2. Добавете следната карта във вашия Lovelace дашборд:**

След като имате помощника, добавете този код към вашия дашборд чрез опцията `Add Card` > `Manual`.

```yaml
type: vertical-stack
cards:
  - type: entities
    entities:
      - entity: input_text.youtube_url_input
        name: YouTube URL
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
  - type: entity
    entity: sensor.yt_dlp_downloader_status
    name: Статус на сваляне
  - type: conditional
    conditions:
      - entity: sensor.yt_dlp_downloader_status
        state: Downloading
    card:
      type: gauge
      entity: sensor.yt_dlp_downloader_status
      attribute: progress
      name: Прогрес
      unit: '%'
```

Тази конфигурация ще ви даде поле за въвеждане на URL, два бутона за сваляне (MP3/MP4) и ще показва статуса и прогреса на свалянето.
