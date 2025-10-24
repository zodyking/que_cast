# Que Cast - Smart TTS Proxy for Home Assistant

[![HACS](https://img.shields.io/badge/HACS-Custom%20integration-blue.svg)](https://custom-components.hacs.xyz/)

<p align="center">
  <img src="https://raw.githubusercontent.com/zodyking/que_cast/refs/heads/main/images/banner.png" alt="Que Cast Banner">
</p>

Que Cast enhances Home Assistant with advanced TTS proxying and media queuing. Features include priority queuing, volume ducking, quiet hours, and multi-room support.

## Key Features
- Priority-based queue with interrupt option
- Configurable pre-roll delay and custom sounds
- Day/night volume with quiet hours (e.g., 22:00-07:00)
- Automatic audio ducking for other players
- Multi-TTS engine support (e.g., `tts.speak`, Polly)
- Multi-instance for rooms/zones
- UI-based config (no YAML needed)
- Queue management (clear, skip, size sensor)

## Installation

### Via HACS
1. HACS → Integrations → Custom repositories → Add `https://github.com/zodyking/que_cast` (Category: Integrations).
2. Install "Que Cast" → Restart Home Assistant.
3. Settings → Devices & Services → Add Integration → "Que Cast" → Configure.

### Manual
1. Download [latest ZIP](https://github.com/zodyking/que_cast/releases) → Extract `custom_components/que_cast/` to `config/custom_components/`.
2. Restart Home Assistant.
3. Configure via Settings → Devices & Services → "Que Cast".

## Configuration
- **Name**: Instance identifier (e.g., "Living Room").
- **Media Player**: Target entity (e.g., `media_player.living_room_speaker`).
- **TTS Engine**: Default service (e.g., `tts.speak`).
- **Volumes**: Day (0.0-1.0), Night (0.0-1.0), Quiet Hours.
- **Advanced**: Pre-roll sound URL, delay (ms), ducking, detection mode (timer/state).

## Usage

### Services
**Speak:**
```yaml
service: que_cast.speak
data:
  instance_id: "living_room"
  message: "Dinner is ready!"
  priority: 5
  interrupt: true
