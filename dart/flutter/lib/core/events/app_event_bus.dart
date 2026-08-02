import 'dart:async';

import 'package:city_vibe/core/events/app_event.dart';

/// Шина событий приложения (broadcast).
///
/// В Flutter/Riverpod это привычный аналог EventBus:
/// - эмиттеры (`emit`) не знают про UI;
/// - экраны/root слушают `stream` через `ref.listen` или [appEventsProvider].
///
/// Пример:
/// ```dart
/// ref.read(appEventBusProvider).emit(AppErrorEvent(message: '…'));
///
/// ref.listen<AsyncValue<AppEvent>>(appEventsProvider, (prev, next) {
///   next.whenData((e) { … });
/// });
/// ```
class AppEventBus {
  AppEventBus();

  final StreamController<AppEvent> _controller =
      StreamController<AppEvent>.broadcast();

  Stream<AppEvent> get stream => _controller.stream;

  /// Очередь ещё жива и можно слать события.
  bool get isClosed => _controller.isClosed;

  void emit(AppEvent event) {
    if (_controller.isClosed) return;
    _controller.add(event);
  }

  /// Подписка с фильтром по типу (удобно в сервисах без Riverpod).
  Stream<T> on<T extends AppEvent>() =>
      stream.where((e) => e is T).cast<T>();

  Future<void> dispose() => _controller.close();
}
