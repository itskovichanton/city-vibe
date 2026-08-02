import 'dart:convert';

import 'package:city_vibe/core/api/models/user_models.dart';
import 'package:shared_preferences/shared_preferences.dart';

const _kMilanaProfileKey = 'cityvibe.milana_profile';
const _kMilanaAvatarPathKey = 'cityvibe.milana_avatar_path';
const _kMilanaAvatarStorageKey = 'cityvibe.milana_avatar_storage_key';

/// Локальный кэш служебного аккаунта Миланы (профиль + путь к файлу аватара).
abstract class MilanaLocalStore {
  Future<UserProfile?> readProfile();

  Future<String?> readAvatarPath();

  Future<String?> readAvatarStorageKey();

  Future<void> saveProfile(UserProfile profile);

  Future<void> saveAvatar({required String localPath, required String storageKey});

  Future<void> clear();
}

class SharedPrefsMilanaLocalStore implements MilanaLocalStore {
  SharedPrefsMilanaLocalStore(this._prefs);

  final SharedPreferences _prefs;

  @override
  Future<UserProfile?> readProfile() async {
    final raw = _prefs.getString(_kMilanaProfileKey);
    if (raw == null || raw.isEmpty) return null;
    try {
      return UserProfile.fromJson(
        Map<String, dynamic>.from(jsonDecode(raw) as Map),
      );
    } catch (_) {
      return null;
    }
  }

  @override
  Future<String?> readAvatarPath() async {
    return _prefs.getString(_kMilanaAvatarPathKey);
  }

  @override
  Future<String?> readAvatarStorageKey() async {
    return _prefs.getString(_kMilanaAvatarStorageKey);
  }

  @override
  Future<void> saveProfile(UserProfile profile) async {
    await _prefs.setString(_kMilanaProfileKey, jsonEncode(profile.toJson()));
  }

  @override
  Future<void> saveAvatar({
    required String localPath,
    required String storageKey,
  }) async {
    await _prefs.setString(_kMilanaAvatarPathKey, localPath);
    await _prefs.setString(_kMilanaAvatarStorageKey, storageKey);
  }

  @override
  Future<void> clear() async {
    await _prefs.remove(_kMilanaProfileKey);
    await _prefs.remove(_kMilanaAvatarPathKey);
    await _prefs.remove(_kMilanaAvatarStorageKey);
  }
}

Future<MilanaLocalStore> createMilanaLocalStore() async {
  final prefs = await SharedPreferences.getInstance();
  return SharedPrefsMilanaLocalStore(prefs);
}
