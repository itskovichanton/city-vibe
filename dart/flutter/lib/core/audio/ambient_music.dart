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

  /// Запуск при старте приложения: lofi1 по кругу.
  static Future<void> start() async {
    await _player.setAsset(startupTrack);
    await _player.setLoopMode(LoopMode.one);
    await _player.setVolume(0.55);
    await _player.play();
  }

  static Future<void> stop() => _player.stop();

  static Future<void> dispose() => _player.dispose();
}
