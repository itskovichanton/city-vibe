import 'package:city_vibe/core/api/models/city.dart';
import 'package:city_vibe/core/api/models/place_category.dart';
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

  /// `GET /categories` — справочник категорий мест.
  Future<List<PlaceCategory>> getCategories({int? limit}) {
    return _http.get(
      '/categories',
      parse: (data) {
        final list = data as List<dynamic>;
        final items = list
            .whereType<Map>()
            .map((e) => PlaceCategory.fromJson(Map<String, dynamic>.from(e)))
            .where((c) => c.isActive)
            .toList(growable: false)
          ..sort((a, b) => a.sortOrder.compareTo(b.sortOrder));
        if (limit != null && limit > 0 && items.length > limit) {
          return items.sublist(0, limit);
        }
        return items;
      },
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
