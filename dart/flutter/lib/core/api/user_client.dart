import 'package:city_vibe/core/api/models/user_models.dart';
import 'package:city_vibe/core/network/api_http.dart';
import 'package:dio/dio.dart';

/// User-методы gateway (`/users/*`).
class UserClient {
  UserClient(this._http);

  final ApiHttp _http;

  Future<UserProfile> getUser(int userId) {
    return _http.get(
      '/users/$userId',
      parse: (data) =>
          UserProfile.fromJson(Map<String, dynamic>.from(data as Map)),
    );
  }

  Future<UserProfile> updateProfile(
    int userId, {
    String? name,
    List<String>? favoriteCategories,
  }) {
    return _http.patch(
      '/users/$userId',
      body: {
        if (name != null) 'name': name,
        if (favoriteCategories != null)
          'favorite_categories': favoriteCategories,
      },
      parse: (data) =>
          UserProfile.fromJson(Map<String, dynamic>.from(data as Map)),
    );
  }

  Future<UserProfile> updateBio(int userId, {required String longBio}) {
    return _http.put(
      '/users/$userId/bio',
      body: {'long_bio': longBio},
      parse: (data) =>
          UserProfile.fromJson(Map<String, dynamic>.from(data as Map)),
    );
  }

  Future<UserProfile> completeOnboarding(int userId) {
    return _http.post(
      '/users/$userId/onboarding/complete',
      parse: (data) =>
          UserProfile.fromJson(Map<String, dynamic>.from(data as Map)),
    );
  }

  Future<UserProfile> uploadAvatar({
    required int userId,
    required String filePath,
    String filename = 'avatar.jpg',
  }) {
    return _http.post(
      '/users/$userId/avatar',
      body: FormData.fromMap({
        'file': MultipartFile.fromFileSync(filePath, filename: filename),
      }),
      parse: (data) =>
          UserProfile.fromJson(Map<String, dynamic>.from(data as Map)),
    );
  }
}
