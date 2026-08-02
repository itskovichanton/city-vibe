import 'package:city_vibe/core/api/models/user_models.dart';
import 'package:city_vibe/core/network/api_http.dart';

/// Милана — служебный аккаунт и NL-поиск (`/milana/*`).
class MilanaClient {
  MilanaClient(this._http);

  final ApiHttp _http;

  /// `GET /milana/account` — профиль служебного аккаунта Миланы.
  Future<UserProfile> getAccount() {
    return _http.get(
      '/milana/account',
      parse: (data) =>
          UserProfile.fromJson(Map<String, dynamic>.from(data as Map)),
    );
  }
}
