import 'package:city_vibe/core/api/models/auth_models.dart';
import 'package:city_vibe/core/api/models/user_models.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('UserStatus', () {
    test('fromApi maps ACTIVE and BANNED', () {
      expect(UserStatus.fromApi('ACTIVE'), UserStatus.active);
      expect(UserStatus.fromApi('active'), UserStatus.active);
      expect(UserStatus.fromApi('BANNED'), UserStatus.banned);
      expect(UserStatus.fromApi(null), UserStatus.active);
    });

    test('apiValue round-trip', () {
      expect(UserStatus.active.apiValue, 'ACTIVE');
      expect(UserStatus.banned.apiValue, 'BANNED');
    });
  });

  group('UserProfile', () {
    test('fromJson / toJson preserves onboarding fields', () {
      const original = UserProfile(
        id: 42,
        name: 'Алексей',
        status: UserStatus.active,
        gender: Gender.male,
        longBio: 'Люблю парки',
        favoriteCategories: ['bars', 'cafes'],
        onboardingCompleted: false,
        avatarUrl: 'http://localhost/avatar.jpg',
        cityId: 3,
      );

      final restored = UserProfile.fromJson(original.toJson());
      expect(restored.id, 42);
      expect(restored.name, 'Алексей');
      expect(restored.status, UserStatus.active);
      expect(restored.longBio, 'Люблю парки');
      expect(restored.favoriteCategories, ['bars', 'cafes']);
      expect(restored.onboardingCompleted, false);
      expect(restored.avatarUrl, 'http://localhost/avatar.jpg');
      expect(restored.cityId, 3);
    });

    test('copyWith updates name and categories', () {
      const user = UserProfile(id: 1, name: 'Old');
      final next = user.copyWith(
        name: 'New',
        favoriteCategories: ['theaters'],
      );
      expect(next.name, 'New');
      expect(next.favoriteCategories, ['theaters']);
      expect(user.name, 'Old');
    });

    test('fromJson parses BANNED status', () {
      final user = UserProfile.fromJson({
        'id': 5,
        'name': 'Blocked',
        'status': 'BANNED',
        'gender': 'male',
      });
      expect(user.status, UserStatus.banned);
      expect(user.status.isBanned, isTrue);
    });
  });
}
