import 'dart:async';

import 'package:city_vibe/core/api/models/user_models.dart';
import 'package:city_vibe/core/api/user_client.dart';
import 'package:city_vibe/core/user/user_local_store.dart';

/// Профиль пользователя: cache-first + синхронизация с API.
class UserRepository {
  UserRepository({
    required UserClient client,
    required UserLocalStore store,
  })  : _client = client,
        _store = store;

  final UserClient _client;
  final UserLocalStore _store;

  Future<void>? _refreshInFlight;

  UserProfile? _memoryCache;

  /// Последний известный профиль в памяти (без await).
  UserProfile? get cached => _memoryCache;

  Future<UserProfile?> readCached() async {
    _memoryCache ??= await _store.read();
    return _memoryCache;
  }

  /// Сохранить профиль (после ответа API или локальной мутации).
  Future<UserProfile> save(UserProfile user) async {
    _memoryCache = user;
    await _store.save(user);
    return user;
  }

  Future<void> clear() async {
    _memoryCache = null;
    await _store.clear();
  }

  /// Прочитать → изменить → сохранить (optimistic / offline edits).
  Future<UserProfile> updateLocal(
    UserProfile Function(UserProfile current) mutate,
  ) async {
    final current = await readCached();
    if (current == null) {
      throw StateError('Нет сохранённого профиля пользователя');
    }
    return save(mutate(current));
  }

  /// GET /users/{id} + сохранить. С кэшем — отдаём сразу и обновляем в фоне.
  Future<UserProfile> fetchAndCache(
    int userId, {
    bool forceRefresh = false,
  }) async {
    final cached = await readCached();
    if (!forceRefresh &&
        cached != null &&
        cached.id == userId &&
        !cached.deleted) {
      unawaited(_refreshFromNetwork(userId));
      return cached;
    }

    return _fetchAndSave(userId);
  }

  Future<UserProfile> _fetchAndSave(int userId) async {
    final remote = await _client.getUser(userId);
    return save(remote);
  }

  Future<void> _refreshFromNetwork(int userId) {
    final inFlight = _refreshInFlight;
    if (inFlight != null) return inFlight;
    final future = () async {
      try {
        await _fetchAndSave(userId);
      } catch (_) {
        // Тихий refresh — оставляем старый кэш.
      }
    }().whenComplete(() {
      _refreshInFlight = null;
    });
    _refreshInFlight = future;
    return future;
  }

  Future<UserProfile> updateBio(int userId, {required String longBio}) async {
    final user = await _client.updateBio(userId, longBio: longBio);
    return save(user);
  }

  Future<UserProfile> updateProfile(
    int userId, {
    String? name,
    List<String>? favoriteCategories,
  }) async {
    final user = await _client.updateProfile(
      userId,
      name: name,
      favoriteCategories: favoriteCategories,
    );
    return save(user);
  }

  Future<UserProfile> completeOnboarding(int userId) async {
    final user = await _client.completeOnboarding(userId);
    return save(user);
  }

  Future<UserProfile> uploadAvatar({
    required int userId,
    required String filePath,
    String filename = 'avatar.jpg',
  }) async {
    final user = await _client.uploadAvatar(
      userId: userId,
      filePath: filePath,
      filename: filename,
    );
    return save(user);
  }
}
