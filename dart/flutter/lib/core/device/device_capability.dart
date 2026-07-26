import 'package:device_info_plus/device_info_plus.dart';
import 'package:flutter/foundation.dart';

/// Возможности текущего устройства: тяжёлые фичи на слабых телефонах отключаем.
///
/// Вызови [DeviceCapability.init] один раз в `main()` до `runApp`.
/// Дальше удобно: [isWeakDevice] / [DeviceCapability.isWeak].
class DeviceCapability {
  DeviceCapability._({required this.weak});

  /// `true` — устройство слабое: лучше без тяжёлых анимаций / эффектов.
  final bool weak;

  static DeviceCapability _instance = DeviceCapability._(weak: false);

  static DeviceCapability get current => _instance;

  static bool get isWeak => _instance.weak;

  /// Определяет «слабость» по платформенным сигналам.
  static Future<DeviceCapability> init() async {
    final weak = await _detectWeak();
    return _instance = DeviceCapability._(weak: weak);
  }

  static Future<bool> _detectWeak() async {
    if (kIsWeb) return false;

    final plugin = DeviceInfoPlugin();

    switch (defaultTargetPlatform) {
      case TargetPlatform.android:
        final android = await plugin.androidInfo;
        // Системный Low RAM + очень старые API.
        return android.isLowRamDevice || android.version.sdkInt < 28;

      case TargetPlatform.iOS:
        final ios = await plugin.iosInfo;
        return _isWeakIosMachine(ios.utsname.machine);

      // Десктоп / прочее — не считаем слабыми.
      case TargetPlatform.macOS:
      case TargetPlatform.windows:
      case TargetPlatform.linux:
      case TargetPlatform.fuchsia:
        return false;
    }
  }

  /// iPhone ≤ X / старые iPad — слабые для непрерывного GPU-скролла.
  ///
  /// `utsname.machine`: `iPhone10,3`, `iPad7,5`, …
  static bool _isWeakIosMachine(String machine) {
    final m = machine.toLowerCase();
    final phone = RegExp(r'^iphone(\d+)').firstMatch(m);
    if (phone != null) {
      final gen = int.tryParse(phone.group(1)!) ?? 99;
      // iPhone10 = 8 / X; iPhone11 = XR/XS и новее — ок.
      return gen <= 10;
    }
    final pad = RegExp(r'^ipad(\d+)').firstMatch(m);
    if (pad != null) {
      final gen = int.tryParse(pad.group(1)!) ?? 99;
      return gen <= 6;
    }
    // Симулятор / неизвестная модель — не режем фичи.
    return false;
  }
}

/// Глобальный хелпер: слабый ли телефон (после [DeviceCapability.init]).
bool isWeakDevice() => DeviceCapability.isWeak;
