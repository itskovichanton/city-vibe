import 'dart:async';

import 'package:city_vibe/app.dart';
import 'package:city_vibe/core/app/app_identity.dart';
import 'package:city_vibe/core/audio/ambient_music.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

Future<void> main() async {
  runZonedGuarded(() async {
    WidgetsFlutterBinding.ensureInitialized();
    _installCrashLogging();

    await SystemChrome.setEnabledSystemUIMode(SystemUiMode.edgeToEdge);
    SystemChrome.setSystemUIOverlayStyle(
      const SystemUiOverlayStyle(
        statusBarColor: Colors.transparent,
        systemNavigationBarColor: Colors.transparent,
        systemNavigationBarContrastEnforced: false,
        statusBarIconBrightness: Brightness.light,
        systemNavigationBarIconBrightness: Brightness.light,
        statusBarBrightness: Brightness.dark,
      ),
    );

    unawaited(_warmUpInBackground());

    runApp(const ProviderScope(child: CityVibeApp()));

    WidgetsBinding.instance.addPostFrameCallback((_) {
      unawaited(AmbientMusic.startSafely());
    });
  }, _logUncaughtZoneError);
}

/// Не блокирует первый кадр: identity и ориентация подтягиваются параллельно UI.
Future<void> _warmUpInBackground() async {
  try {
    await Future.wait([
      AppIdentity.init(),
      SystemChrome.setPreferredOrientations([
        DeviceOrientation.portraitUp,
      ]),
    ]).timeout(const Duration(seconds: 5));
  } on TimeoutException {
    // platform channel подвис — UI уже работает.
  } catch (_) {
    // дефолты [AppIdentity].
  }
}

/// Dart/async ошибки, которые не поймал Flutter framework.
void _logUncaughtZoneError(Object error, StackTrace stack) {
  debugPrint('UNCAUGHT (zone): $error');
  debugPrintStack(stackTrace: stack);
}

void _installCrashLogging() {
  FlutterError.onError = (details) {
    FlutterError.presentError(details);
    debugPrint('FlutterError: ${details.exceptionAsString()}');
    if (details.stack != null) {
      debugPrintStack(stackTrace: details.stack);
    }
  };

  PlatformDispatcher.instance.onError = (error, stack) {
    debugPrint('PlatformDispatcher.onError: $error');
    debugPrintStack(stackTrace: stack);
    return true;
  };
}
