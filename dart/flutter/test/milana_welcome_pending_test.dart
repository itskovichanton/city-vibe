import 'package:city_vibe/features/onboarding/milana_welcome_pending.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('MilanaWelcomeCompletedNotifier', () {
    setUp(() async {
      SharedPreferences.setMockInitialValues({});
    });

    test('starts not ready until syncForUser completes', () {
      final container = ProviderContainer();
      addTearDown(container.dispose);

      expect(container.read(milanaWelcomeCompletedProvider).ready, isFalse);
      expect(container.read(milanaWelcomePendingProvider), isFalse);
    });

    test('syncForUser resets flag when onboarding is incomplete', () async {
      final container = ProviderContainer();
      addTearDown(container.dispose);

      final notifier = container.read(milanaWelcomeCompletedProvider.notifier);

      await notifier.syncForUser(7, onboardingCompleted: true);
      await notifier.markCompleted();
      expect(container.read(milanaWelcomeCompletedProvider).completed, isTrue);

      await notifier.syncForUser(7, onboardingCompleted: false);
      expect(container.read(milanaWelcomeCompletedProvider).completed, isFalse);
      expect(container.read(milanaWelcomePendingProvider), isTrue);
    });

    test('syncForUser keeps separate flags per user id', () async {
      final container = ProviderContainer();
      addTearDown(container.dispose);

      final notifier = container.read(milanaWelcomeCompletedProvider.notifier);

      await notifier.syncForUser(7, onboardingCompleted: true);
      await notifier.markCompleted();

      await notifier.syncForUser(42, onboardingCompleted: true);
      expect(container.read(milanaWelcomeCompletedProvider).completed, isFalse);
      expect(container.read(milanaWelcomePendingProvider), isTrue);
    });

    test('completed user does not appear pending after sync', () async {
      final container = ProviderContainer();
      addTearDown(container.dispose);

      final notifier = container.read(milanaWelcomeCompletedProvider.notifier);
      await notifier.syncForUser(7, onboardingCompleted: true);
      await notifier.markCompleted();

      expect(container.read(milanaWelcomeReadyProvider), isTrue);
      expect(container.read(milanaWelcomePendingProvider), isFalse);
    });
  });
}
