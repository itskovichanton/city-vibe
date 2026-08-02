import 'package:city_vibe/core/api/api_providers.dart';
import 'package:city_vibe/core/api/models/user_models.dart';
import 'package:city_vibe/core/auth/session_guard.dart';
import 'package:city_vibe/core/network/api_exception.dart';
import 'package:city_vibe/core/user/user_local_store.dart';
import 'package:city_vibe/core/user/user_repository.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final userLocalStoreProvider = FutureProvider<UserLocalStore>((ref) async {
  return createUserLocalStore();
});

final userRepositoryProvider = FutureProvider<UserRepository>((ref) async {
  final store = await ref.watch(userLocalStoreProvider.future);
  return UserRepository(
    client: ref.watch(userClientProvider),
    store: store,
  );
});

/// Текущий профиль пользователя — единый источник правды для UI.
///
/// `ref.watch(currentUserProvider)` — перерисовка при смене имени, аватара и т.д.
final currentUserProvider =
    AsyncNotifierProvider<CurrentUserNotifier, UserProfile?>(
  CurrentUserNotifier.new,
);

class CurrentUserNotifier extends AsyncNotifier<UserProfile?> {
  Future<UserRepository> get _repo => ref.read(userRepositoryProvider.future);

  @override
  Future<UserProfile?> build() async {
    final repo = await _repo;
    return repo.readCached();
  }

  Future<UserProfile?> load(int userId, {bool forceRefresh = false}) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final repo = await _repo;
      final user = await repo.fetchAndCache(userId, forceRefresh: forceRefresh);
      SessionGuard.instance.rejectIfBanned(user);
      return user;
    });
    final error = state.error;
    if (error is ApiException && error.requiresReLogin) {
      SessionGuard.instance.handleAuthHttpError(error);
    }
    return state.value;
  }

  /// Применить профиль из ответа API (bio, avatar, onboarding…).
  Future<UserProfile> apply(UserProfile user) async {
    SessionGuard.instance.rejectIfBanned(user);
    final repo = await _repo;
    final saved = await repo.save(user);
    state = AsyncData(saved);
    return saved;
  }

  /// Локальная мутация без round-trip (optimistic UI).
  Future<UserProfile> updateLocal(
    UserProfile Function(UserProfile current) mutate,
  ) async {
    final repo = await _repo;
    final next = await repo.updateLocal(mutate);
    state = AsyncData(next);
    return next;
  }

  Future<UserProfile> updateBio({required String longBio}) async {
    final userId = state.value?.id;
    if (userId == null) throw StateError('Нет текущего пользователя');
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final repo = await _repo;
      return repo.updateBio(userId, longBio: longBio);
    });
    final user = state.requireValue;
    if (user == null) throw StateError('Не удалось обновить bio');
    return user;
  }

  Future<UserProfile> updateProfile({
    String? name,
    List<String>? favoriteCategories,
  }) async {
    final userId = state.value?.id;
    if (userId == null) throw StateError('Нет текущего пользователя');
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final repo = await _repo;
      final user = await repo.updateProfile(
        userId,
        name: name,
        favoriteCategories: favoriteCategories,
      );
      SessionGuard.instance.rejectIfBanned(user);
      return user;
    });
    final user = state.requireValue;
    if (user == null) throw StateError('Не удалось обновить профиль');
    return user;
  }

  Future<UserProfile> completeOnboarding() async {
    final userId = state.value?.id;
    if (userId == null) throw StateError('Нет текущего пользователя');
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final repo = await _repo;
      return repo.completeOnboarding(userId);
    });
    final user = state.requireValue;
    if (user == null) throw StateError('Не удалось завершить onboarding');
    return user;
  }

  Future<UserProfile> uploadAvatar({
    required String filePath,
    String filename = 'avatar.jpg',
  }) async {
    final userId = state.value?.id;
    if (userId == null) throw StateError('Нет текущего пользователя');
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final repo = await _repo;
      return repo.uploadAvatar(
        userId: userId,
        filePath: filePath,
        filename: filename,
      );
    });
    final user = state.requireValue;
    if (user == null) throw StateError('Не удалось загрузить аватар');
    return user;
  }

  Future<void> clear() async {
    final repo = await _repo;
    await repo.clear();
    state = const AsyncData(null);
  }
}
