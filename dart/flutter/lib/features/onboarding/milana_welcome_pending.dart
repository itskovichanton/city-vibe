import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

const _kMilanaWelcomeCompleted = 'cityvibe.milana_welcome_completed';

/// `true` — пользователь уже нажал «Начать путешествие с Миланой».
final milanaWelcomeCompletedProvider =
    NotifierProvider<MilanaWelcomeCompletedNotifier, bool>(
  MilanaWelcomeCompletedNotifier.new,
);

class MilanaWelcomeCompletedNotifier extends Notifier<bool> {
  SharedPreferences? _prefs;

  @override
  bool build() {
    _restore();
    return false;
  }

  Future<void> _restore() async {
    _prefs = await SharedPreferences.getInstance();
    state = _prefs!.getBool(_kMilanaWelcomeCompleted) ?? false;
  }

  Future<void> markCompleted() async {
    state = true;
    final prefs = _prefs ?? await SharedPreferences.getInstance();
    _prefs = prefs;
    await prefs.setBool(_kMilanaWelcomeCompleted, true);
  }

  Future<void> reset() async {
    state = false;
    final prefs = _prefs ?? await SharedPreferences.getInstance();
    _prefs = prefs;
    await prefs.remove(_kMilanaWelcomeCompleted);
  }
}

/// Совместимость: «pending» = приветствие ещё не пройдено.
final milanaWelcomePendingProvider = Provider<bool>((ref) {
  return !ref.watch(milanaWelcomeCompletedProvider);
});
