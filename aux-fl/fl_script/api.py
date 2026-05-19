"""Thin wrappers around FL Studio's internal Python API.

This module runs inside FL Studio's MIDI scripting runtime. Keep it stdlib-only
apart from FL's built-in modules.
"""

import channels
import mixer
import patterns
import transport


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def get_state():
    return {
        "tempo": transport.getTempo(),
        "is_playing": transport.isPlaying(),
        "song_pos": transport.getSongPos(),
        "master_volume": mixer.getTrackVolume(0),
        "mixer": _get_mixer(),
        "channels": _get_channels(),
        "patterns": _get_patterns(),
    }


def _get_mixer():
    count = mixer.trackCount()
    tracks = []
    for index in range(min(count, 64)):
        tracks.append(
            {
                "index": index,
                "name": mixer.getTrackName(index),
                "volume": mixer.getTrackVolume(index),
                "pan": mixer.getTrackPan(index),
                "muted": not mixer.isTrackEnabled(index),
            }
        )
    return tracks


def _get_channels():
    result = []
    for index in range(channels.channelCount()):
        result.append(
            {
                "index": index,
                "name": channels.getChannelName(index),
                "volume": channels.getChannelVolume(index),
                "pan": channels.getChannelPan(index),
                "muted": channels.isChannelMuted(index),
                "pitch": channels.getChannelPitch(index),
            }
        )
    return result


def _get_patterns():
    result = []
    for index in range(patterns.patternCount()):
        result.append(
            {
                "index": index,
                "name": patterns.getPatternName(index),
                "length": patterns.getPatternLength(index),
            }
        )
    return result


def set_mixer_volume(track, volume):
    mixer.setTrackVolume(int(track), clamp(float(volume), 0.0, 1.0))


def set_mixer_pan(track, pan):
    mixer.setTrackPan(int(track), clamp(float(pan), -1.0, 1.0))


def mute_track(track, muted):
    if bool(muted):
        mixer.muteTrack(int(track))
    else:
        mixer.enableTrack(int(track))


def set_channel_volume(channel, volume):
    channels.setChannelVolume(int(channel), clamp(float(volume), 0.0, 1.0))


def set_channel_pan(channel, pan):
    channels.setChannelPan(int(channel), clamp(float(pan), -1.0, 1.0))


def set_channel_pitch(channel, semitones):
    channels.setChannelPitch(int(channel), clamp(float(semitones), -48.0, 48.0))


def mute_channel(channel, muted):
    channels.muteChannel(int(channel), bool(muted))


def set_tempo(bpm):
    transport.setTempo(clamp(float(bpm), 40.0, 999.0))


def play():
    transport.start()


def stop():
    transport.stop()


def jump_to_pattern(index):
    patterns.jumpToPattern(int(index))
