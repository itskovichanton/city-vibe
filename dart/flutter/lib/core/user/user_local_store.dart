import 'dart:convert';

import 'package:city_vibe/core/api/models/user_models.dart';
import 'package:shared_preferences/shared_preferences.dart';

const _kCurrentUserKey = 'cityvibe.current_user_profile';

/// Локальный кэш профиля текущего пользователя (SharedPreferences).
abstract class UserLocalStore {
  Future<UserProfile?> read();

  Future<void> save(UserProfile user);

  Future<void> clear();
}

class SharedPrefsUserLocalStore implements UserLocalStore {
  SharedPrefsUserLocalStore(this._prefs);

  final SharedPreferences _prefs;

  @override
  Future<UserProfile?> read() async {
    final raw = _prefs.getString(_kCurrentUserKey);
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
  Future<void> save(UserProfile user) async {
    await _prefs.setString(_kCurrentUserKey, jsonEncode(user.toJson()));
  }

  @override
  Future<void> clear() async {
    await _prefs.remove(_kCurrentUserKey);
  }
}

Future<UserLocalStore> createUserLocalStore() async {
  final prefs = await SharedPreferences.getInstance();
  return SharedPrefsUserLocalStore(prefs);
}
