import 'dart:async';
import 'dart:io';

import 'package:city_vibe/core/api/milana_client.dart';
import 'package:city_vibe/core/milana/milana_account.dart';
import 'package:city_vibe/core/milana/milana_local_store.dart';
import 'package:city_vibe/core/network/media_url_resolver.dart';
import 'package:dio/dio.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

/// Служебный аккаунт Миланы: API + локальный кэш профиля и файла аватара.
class MilanaRepository {
  MilanaRepository({
    required MilanaClient client,
    required MilanaLocalStore store,
    required Dio dio,
  })  : _client = client,
        _store = store,
        _dio = dio;

  final MilanaClient _client;
  final MilanaLocalStore _store;
  final Dio _dio;

  Future<MilanaAccount>? _loadInFlight;

  Future<MilanaAccount> loadAccount({bool forceRefresh = false}) async {
    if (!forceRefresh) {
      final cached = await _readCachedAccount();
      if (cached != null) {
        unawaited(_refreshInBackground());
        return cached;
      }
    }

    final inFlight = _loadInFlight;
    if (inFlight != null) return inFlight;

    final future = _fetchAndCache().whenComplete(() {
      _loadInFlight = null;
    });
    _loadInFlight = future;
    return future;
  }

  Future<void> _refreshInBackground() async {
    try {
      await _fetchAndCache();
    } catch (_) {
      // Тихий refresh — оставляем локальный кэш.
    }
  }

  Future<MilanaAccount?> _readCachedAccount() async {
    final profile = await _store.readProfile();
    if (profile == null) return null;

    final avatarPath = await _store.readAvatarPath();
    if (avatarPath != null && !File(avatarPath).existsSync()) {
      return MilanaAccount(profile: profile);
    }

    return MilanaAccount(profile: profile, avatarLocalPath: avatarPath);
  }

  Future<MilanaAccount> _fetchAndCache() async {
    final remote = await _client.getAccount();
    await _store.saveProfile(remote);

    final avatarPath = await _syncAvatarFile(remote.avatarUrl);
    return MilanaAccount(profile: remote, avatarLocalPath: avatarPath);
  }

  Future<String?> _syncAvatarFile(String? storageKey) async {
    if (storageKey == null || storageKey.isEmpty) return null;

    final url = MediaUrlResolver.resolve(storageKey);
    if (url == null) return null;

    final cachedKey = await _store.readAvatarStorageKey();
    final cachedPath = await _store.readAvatarPath();
    if (cachedKey == storageKey &&
        cachedPath != null &&
        File(cachedPath).existsSync()) {
      return cachedPath;
    }

    final dir = await getApplicationDocumentsDirectory();
    final file = File(p.join(dir.path, 'milana_avatar.jpg'));
    await _dio.download(url, file.path);
    await _store.saveAvatar(localPath: file.path, storageKey: storageKey);
    return file.path;
  }

  Future<void> clear() async {
    _loadInFlight = null;
    final path = await _store.readAvatarPath();
    if (path != null) {
      try {
        final file = File(path);
        if (await file.exists()) await file.delete();
      } catch (_) {}
    }
    await _store.clear();
  }
}
