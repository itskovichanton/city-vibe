import 'package:flutter/foundation.dart';
import 'package:package_info_plus/package_info_plus.dart';

/// Идентичность официального клиента: OS + версия → User-Agent для API.
///
/// Вызови [AppIdentity.init] один раз в `main()` до `runApp`.
/// Формат: `cityvibe-official-client:<os=android|ios|…>:v0.1.0`
class AppIdentity {
  AppIdentity._({
    required this.os,
    required this.version,
    required this.buildNumber,
    required this.userAgent,
  });

  final String os;
  final String version;
  final String buildNumber;

  /// Готовый заголовок `User-Agent` для всех HTTP-запросов.
  final String userAgent;

  static AppIdentity _instance = AppIdentity._(
    os: _detectOs(),
    version: '0.0.0',
    buildNumber: '0',
    userAgent: _buildUserAgent(_detectOs(), '0.0.0'),
  );

  static AppIdentity get current => _instance;

  static String get userAgentValue => _instance.userAgent;

  static Future<AppIdentity> init() async {
    final info = await PackageInfo.fromPlatform();
    final os = _detectOs();
    final version = info.version;
    final build = info.buildNumber;
    return _instance = AppIdentity._(
      os: os,
      version: version,
      buildNumber: build,
      userAgent: _buildUserAgent(os, version),
    );
  }

  static String _buildUserAgent(String os, String version) {
    return 'cityvibe-official-client:os=$os:v=$version';
  }

  static String _detectOs() {
    if (kIsWeb) return 'web';
    return switch (defaultTargetPlatform) {
      TargetPlatform.android => 'android',
      TargetPlatform.iOS => 'ios',
      TargetPlatform.macOS => 'macos',
      TargetPlatform.windows => 'windows',
      TargetPlatform.linux => 'linux',
      TargetPlatform.fuchsia => 'fuchsia',
    };
  }
}
