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

## Repository Structure

This repo follows standard HACS/Home Assistant custom integration layout:
