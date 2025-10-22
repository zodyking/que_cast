# TTS Proxy — Home Assistant Custom Integration

**Queued, no-clash TTS with per-room queues, day/night volumes, ducking, and a simple `tts_proxy.speak` service.**

![badge](https://img.shields.io/badge/HA-Custom%20Component-blue) ![badge](https://img.shields.io/github/v/release/your-user/tts_proxy)

## Features
- **True serialization** — one TTS at a time per proxy (room)
- **Multi-room** — create multiple proxy instances, each with its own queue
- **Day/Night volumes** with quiet hours
- **Pre-roll** to avoid first-syllable clipping
- **Ducking** — lower other media players while TTS is speaking
- **Buttons** — Clear Queue & Skip Current
- **Queue size sensor**

## Installation (HACS)
1. In HACS, add this repository as a **Custom repository** (category **Integration**): `https://github.com/your-user/tts_proxy`
2. Install **TTS Proxy**.
3. Restart Home Assistant.
4. Go to **Settings → Devices & Services → Add Integration → TTS Proxy**.

## Manual install
- Copy `custom_components/tts_proxy/` into your Home Assistant `custom_components/` directory.
- Restart Home Assistant and add the integration from the UI.

## Configuration (UI)
For each room/queue:
- **Target media player** (default speaker for the queue)
- **TTS service** (e.g., `tts.speak`, `google_cloud_say.speak`)
- Optional **default language** and **options JSON** for your TTS provider
- **Quiet hours** window, **day/night** volumes, and **pre-roll (ms)**
- **Ducking**: enable, targets (comma-separated), duck volume, restore delay
- **Done detection**: by player **state** (default) or **timer** with a max seconds cap

## Service: `tts_proxy.speak`
```yaml
service: tts_proxy.speak
data:
  message: "Front door opened."
  media_player_entity_id: media_player.living_room
  # Optional:
  # proxy_id: "Living Room Proxy"    # (entry title or entry_id)
  # interrupt: true                  # stop current audio & clear queue
  # priority: 5                      # higher runs sooner (FIFO among equals)
  # volume_override: 0.55            # bypass day/night
  # pre_roll_ms: 200                 # override proxy default
  # language: en-US
  # options: { voice: "studio" }
```

### Example automations
```yaml
- alias: Door announce
  trigger:
    - platform: state
      entity_id: binary_sensor.front_door
      to: "on"
  action:
    - service: tts_proxy.speak
      data:
        message: "Front door opened."
        media_player_entity_id: media_player.hallway_display
```

## Entities
- `sensor.<proxy_name>_queue` — queue size
- `button.<proxy_name>_clear_queue`
- `button.<proxy_name>_skip_current`

## Troubleshooting
- **No speech?** Ensure your TTS service path is correct (e.g., `tts.speak`) and your target media player is online.
- **Overlapping audio?** Use `interrupt: true` for urgent announcements; otherwise FIFO prevents clashes.
- **Clipped openings?** Increase **pre_roll_ms** to 200–300ms.
- **Provider doesn't toggle to `playing`?** In Options, set **Detection** to **timer** and pick a cap near your average clip length.

---

MIT © You