import 'package:city_vibe/core/user/user_local_store.dart';
import 'package:city_vibe/core/api/models/user_models.dart';
import 'package:flutter_test/flutter_test.dart';

/// In-memory store для тестов репозитория (без SharedPreferences).
class MemoryUserLocalStore implements UserLocalStore {
  UserProfile? _cached;

  @override
  Future<void> clear() async {
    _cached = null;
  }

  @override
  Future<UserProfile?> read() async => _cached;

  @override
  Future<void> save(UserProfile user) async {
    _cached = user;
  }
}

void main() {
  group('UserLocalStore', () {
    test('save / read round-trip', () async {
      final store = MemoryUserLocalStore();
      expect(await store.read(), isNull);

      const profile = UserProfile(
        id: 10,
        name: 'Test',
        favoriteCategories: ['bars'],
        onboardingCompleted: true,
      );
      await store.save(profile);

      final loaded = await store.read();
      expect(loaded?.id, 10);
      expect(loaded?.name, 'Test');
      expect(loaded?.favoriteCategories, ['bars']);
      expect(loaded?.onboardingCompleted, isTrue);
    });
  });
}
