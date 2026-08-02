import 'package:city_vibe/core/events/app_event.dart';
import 'package:city_vibe/core/events/app_event_bus.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Единая шина событий на всё приложение.
final appEventBusProvider = Provider<AppEventBus>((ref) {
  final bus = AppEventBus();
  ref.onDispose(bus.dispose);
  return bus;
});

/// Поток всех [AppEvent] — удобно слушать из UI через `ref.listen`.
final appEventsProvider = StreamProvider<AppEvent>((ref) {
  return ref.watch(appEventBusProvider).stream;
});
