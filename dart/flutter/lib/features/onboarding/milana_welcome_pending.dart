import 'dart:async';

import 'package:city_vibe/core/user/user_providers.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

const _kMilanaWelcomeCompletedPrefix = 'cityvibe.milana_welcome_completed.';
const _kMilanaWelcomeCompletedLegacy = 'cityvibe.milana_welcome_completed';

/// Локальный статус экрана «Знакомство с Миланой».
@immutable
class MilanaWelcomeState {
  const MilanaWelcomeState({
    this.ready = false,
    this.completed = false,
  });

  /// `true` — prefs прочитаны для текущего user id.
  final bool ready;

  /// `true` — пользователь нажал «Начать путешествие с Миланой».
  final bool completed;

  bool get pending => ready && !completed;
}

/// Состояние приветствия Миланы (hydrate из SharedPreferences).
final milanaWelcomeCompletedProvider =
    NotifierProvider<MilanaWelcomeCompletedNotifier, MilanaWelcomeState>(
  MilanaWelcomeCompletedNotifier.new,
);

/// Синхронизирует локальный флаг приветствия с профилем с сервера.
final milanaWelcomeUserSyncProvider = Provider<void>((ref) {
  ref.listen(currentUserProvider, (previous, next) {
    final user = next.valueOrNull;
    unawaited(
      ref.read(milanaWelcomeCompletedProvider.notifier).syncForUser(
            user?.id,
            onboardingCompleted: user?.onboardingCompleted ?? false,
          ),
    );
  });
});

class MilanaWelcomeCompletedNotifier extends Notifier<MilanaWelcomeState> {
  SharedPreferences? _prefs;
  int? _activeUserId;

  @override
  MilanaWelcomeState build() {
    return const MilanaWelcomeState();
  }

  String _keyFor(int userId) => '$_kMilanaWelcomeCompletedPrefix$userId';

  /// Восстанавливает флаг для пользователя или сбрасывает его,
  /// если онбординг на сервере ещё не завершён.
  Future<void> syncForUser(
    int? userId, {
    required bool onboardingCompleted,
  }) async {
    final prefs = _prefs ?? await SharedPreferences.getInstance();
    _prefs = prefs;

    if (userId == null) {
      _activeUserId = null;
      state = const MilanaWelcomeState(ready: true, completed: false);
      return;
    }

    _activeUserId = userId;
    await _dropLegacyKey(prefs);

    if (!onboardingCompleted) {
      await _clearFlag(prefs, userId);
      state = const MilanaWelcomeState(ready: true, completed: false);
      return;
    }

    state = MilanaWelcomeState(
      ready: true,
      completed: prefs.getBool(_keyFor(userId)) ?? false,
    );
  }

  Future<void> markCompleted() async {
    final userId = _activeUserId;
    if (userId == null) return;

    state = const MilanaWelcomeState(ready: true, completed: true);
    final prefs = _prefs ?? await SharedPreferences.getInstance();
    _prefs = prefs;
    await prefs.setBool(_keyFor(userId), true);
  }

  Future<void> reset() async {
    final userId = _activeUserId;
    if (userId == null) {
      state = const MilanaWelcomeState(ready: true, completed: false);
      return;
    }

    final prefs = _prefs ?? await SharedPreferences.getInstance();
    _prefs = prefs;
    await _clearFlag(prefs, userId);
    state = const MilanaWelcomeState(ready: true, completed: false);
  }

  Future<void> _clearFlag(SharedPreferences prefs, int userId) async {
    await prefs.remove(_keyFor(userId));
  }

  Future<void> _dropLegacyKey(SharedPreferences prefs) async {
    if (prefs.containsKey(_kMilanaWelcomeCompletedLegacy)) {
      await prefs.remove(_kMilanaWelcomeCompletedLegacy);
    }
  }
}

/// «Pending» = prefs загружены и экран ещё не пройден.
final milanaWelcomePendingProvider = Provider<bool>((ref) {
  return ref.watch(milanaWelcomeCompletedProvider).pending;
});

/// Prefs для milana-welcome ещё не прочитаны для текущего пользователя.
final milanaWelcomeReadyProvider = Provider<bool>((ref) {
  return ref.watch(milanaWelcomeCompletedProvider).ready;
});
