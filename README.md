# Que Cast - Advanced TTS & Media Proxy for Home Assistant

[![HACS](https://img.shields.io/badge/HACS-Custom%20integration-blue.svg)](https://custom-components.hacs.xyz/)

Que Cast is a powerful Home Assistant custom integration that provides advanced text-to-speech (TTS) proxying and media queue management. It features serialized priority queuing, volume ducking, quiet hours, and multi-room support.

## Features

- **Priority-based Queue**: FIFO with interrupt support for urgent messages
- **Zero-clip Pre-roll**: Configurable delay to prevent audio cutoff
- **Smart Volume Control**: Day/night volumes with quiet hours
- **Audio Ducking**: Automatically lowers other media players during TTS
- **Multi-engine Support**: Works with any HA TTS service (tts.speak, Piper, Polly, etc.)
- **Multiple Instances**: Separate queues per room/zone
- **Custom Pre-roll Sounds**: Add chimes or alerts before messages
- **UI Configuration**: No YAML required - full config flow support
- **Queue Management**: Clear queue, skip current, live queue size sensor

## Installation

### Via HACS

1. Add this repository to HACS custom repositories
2. Search for "Que Cast" and install
3. Restart Home Assistant
4. Configure via Settings > Devices & Services

### Manual Installation

1. Download the ZIP and extract to `custom_components/que_cast/`
2. Restart Home Assistant
3. Configure via Settings > Devices & Services

## Configuration

Add a Que Cast instance via the UI:

### Basic Settings
- **Name**: Friendly name for this instance
- **Media Player**: Target media player entity
- **TTS Engine**: Default TTS service (tts.speak, etc.)

### Volume Settings
- **Day Volume**: Normal daytime volume (0.0-1.0)
- **Night Volume**: Quiet time volume (0.0-1.0)
- **Quiet Hours**: Time window for night volume (e.g., 22:00-07:00)

### Advanced Settings
- **Pre-roll Sound**: URL to custom sound file
- **Pre-roll Delay**: Milliseconds before TTS starts
- **Post-grace Delay**: Delay before restoring volumes
- **Ducking**: Lower other media players during TTS
- **Detection Mode**: State polling or timer-based completion

## Usage

### Service Calls

**Queue TTS Message:**
```yaml
service: que_cast.speak
data:
  instance_id: "living_room"
  message: "Dinner is ready!"
  language: "en-US"
  priority: 5
  interrupt: true
  volume_override: 0.7
