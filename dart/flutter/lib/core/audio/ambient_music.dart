import 'dart:async';

import 'package:audio_session/audio_session.dart';
import 'package:just_audio/just_audio.dart';

/// Фоновая lo-fi музыка приложения.
///
/// Треки лежат в `assets/audio/`. При старте включаем [startupTrack].
class AmbientMusic {
  AmbientMusic._();

  static const startupTrack = 'assets/audio/lofi2.mp3';

  static const tracks = <String>[
    'assets/audio/lofi1.mp3',
    'assets/audio/lofi2.mp3',
    'assets/audio/lofi3.mp3',
    'assets/audio/lofi4.mp3',
    'assets/audio/lofi5.mp3',
  ];

  static final AudioPlayer _player = AudioPlayer();
  static bool _started = false;
  static StreamSubscription<AudioInterruptionEvent>? _interruptionSub;

  /// Запуск при старте приложения: lofi2 по кругу.
  static Future<void> start() async {
    await _configureSession();
    await _player.setAsset(startupTrack);
    await _player.setLoopMode(LoopMode.one);
    await _player.setVolume(0.55);
    await _player.play();
    _started = true;
  }

  /// Не роняет приложение, если аудио-движок недоступен (эмулятор, MIUI).
  static Future<void> startSafely() async {
    try {
      await start();
    } catch (_) {
      // ignore
    }
  }

  /// Продолжить воспроизведение после image picker, смены экрана и т.п.
  static Future<void> ensurePlaying() async {
    if (!_started) return;
    try {
      if (!_player.playing) {
        await _player.play();
      }
    } catch (_) {
      // ignore
    }
  }

  static Future<void> stop() => _player.stop();

  static Future<void> dispose() async {
    await _interruptionSub?.cancel();
    _interruptionSub = null;
    await _player.dispose();
    _started = false;
  }

  static Future<void> _configureSession() async {
    final session = await AudioSession.instance;
    await session.configure(const AudioSessionConfiguration.music());
    _interruptionSub ??= session.interruptionEventStream.listen((event) {
      if (event.begin) return;
      unawaited(ensurePlaying());
    });
  }
}
