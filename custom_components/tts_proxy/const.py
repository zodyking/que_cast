DOMAIN = "tts_proxy"

CONF_TARGET_MEDIA_PLAYER = "target_media_player"
CONF_TTS_SERVICE = "tts_service"
CONF_TTS_DEFAULT_LANGUAGE = "default_language"
CONF_TTS_DEFAULT_OPTIONS = "default_options"
CONF_QUIET_HOURS = "quiet_hours"
CONF_DAY_VOLUME = "day_volume"
CONF_NIGHT_VOLUME = "night_volume"
CONF_PRE_ROLL_MS = "pre_roll_ms"

CONF_DUCK_ENABLE = "duck_enable"
CONF_DUCK_TARGETS = "duck_targets"
CONF_DUCK_VOLUME = "duck_volume"
CONF_RESTORE_AFTER_MS = "restore_after_ms"

CONF_DETECT_DONE_MODE = "detect_done_mode"
CONF_MAX_SPEECH_SECONDS = "max_speech_seconds"

DEFAULTS = {
    CONF_TTS_SERVICE: "tts.speak",
    CONF_TTS_DEFAULT_LANGUAGE: None,
    CONF_TTS_DEFAULT_OPTIONS: {},
    CONF_QUIET_HOURS: "22:00-07:00",
    CONF_DAY_VOLUME: 0.45,
    CONF_NIGHT_VOLUME: 0.20,
    CONF_PRE_ROLL_MS: 150,
    CONF_DUCK_ENABLE: True,
    CONF_DUCK_TARGETS: [],
    CONF_DUCK_VOLUME: 0.15,
    CONF_RESTORE_AFTER_MS: 250,
    CONF_DETECT_DONE_MODE: "state",
    CONF_MAX_SPEECH_SECONDS: 45,
}