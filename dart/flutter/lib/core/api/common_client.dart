import 'package:city_vibe/core/api/models/city.dart';
import 'package:city_vibe/core/network/api_http.dart';

/// Справочники и общие методы gateway (`/cities`, `/health`, …).
class CommonClient {
  CommonClient(this._http);

  final ApiHttp _http;

  /// `GET /cities` — крупные города для выбора при регистрации.
  Future<List<City>> getCities() {
    return _http.get(
      '/cities',
      parse: (data) {
        final list = data as List<dynamic>;
        return list
            .whereType<Map>()
            .map((e) => City.fromJson(Map<String, dynamic>.from(e)))
            .toList(growable: false);
      },
    );
  }

  /// `GET /cities/{id}`
  Future<City> getCity(int cityId) {
    return _http.get(
      '/cities/$cityId',
      parse: (data) => City.fromJson(Map<String, dynamic>.from(data as Map)),
    );
  }

  /// `GET /cities/nearest?lat=&lng=` — ближайший крупный город к GPS.
  Future<City> getNearestCity({required double lat, required double lng}) {
    return _http.get(
      '/cities/nearest',
      query: {'lat': lat, 'lng': lng},
      parse: (data) => City.fromJson(Map<String, dynamic>.from(data as Map)),
    );
  }

  /// `GET /health`
  Future<Map<String, dynamic>> health() {
    return _http.get(
      '/health',
      parse: (data) => Map<String, dynamic>.from(data as Map),
    );
  }
}
