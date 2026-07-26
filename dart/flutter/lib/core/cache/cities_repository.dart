import 'dart:async';
import 'dart:math' as math;

import 'package:city_vibe/core/api/common_client.dart';
import 'package:city_vibe/core/api/models/city.dart';
import 'package:city_vibe/core/cache/city_local_store.dart';
import 'package:city_vibe/core/network/api_exception.dart';

/// Города: cache-first из SQLite, сеть обновляет кэш в фоне.
class CitiesRepository {
  CitiesRepository({
    required CommonClient client,
    required CityLocalStore store,
  })  : _client = client,
        _store = store;

  final CommonClient _client;
  final CityLocalStore _store;

  Future<void>? _refreshInFlight;

  /// Список городов для UI.
  ///
  /// Если кэш не пуст — сразу отдаём его и тихо обновляем с сети.
  /// Если кэш пуст — ждём сеть; при ошибке сети пробрасываем исключение.
  Future<List<City>> getCities({bool forceRefresh = false}) async {
    final cached = await _store.getAll();

    if (cached.isNotEmpty && !forceRefresh) {
      unawaited(_refreshFromNetwork());
      return cached;
    }

    try {
      return await _fetchAndCache();
    } catch (e) {
      if (cached.isNotEmpty) return cached;
      rethrow;
    }
  }

  /// Ближайший город: сначала API, при сбое — расчёт по кэшу (haversine).
  Future<City> getNearestCity({
    required double lat,
    required double lng,
  }) async {
    try {
      final remote = await _client.getNearestCity(lat: lat, lng: lng);
      // Подмешиваем/обновляем одну запись не обязательно; список обновит getCities.
      return remote;
    } on ApiException {
      final local = await _nearestFromCache(lat: lat, lng: lng);
      if (local != null) return local;
      rethrow;
    } catch (_) {
      final local = await _nearestFromCache(lat: lat, lng: lng);
      if (local != null) return local;
      rethrow;
    }
  }

  Future<void> _refreshFromNetwork() {
    final inFlight = _refreshInFlight;
    if (inFlight != null) return inFlight;
    final future = () async {
      try {
        await _fetchAndCache();
      } catch (_) {
        // Тихий refresh: офлайн / 5xx — оставляем старый кэш.
      }
    }().whenComplete(() {
      _refreshInFlight = null;
    });
    _refreshInFlight = future;
    return future;
  }

  Future<List<City>> _fetchAndCache() async {
    final fresh = await _client.getCities();
    await _store.replaceAll(fresh);
    return fresh;
  }

  Future<City?> _nearestFromCache({
    required double lat,
    required double lng,
  }) async {
    final cities = await _store.getAll();
    return findNearestCity(cities, lat: lat, lng: lng);
  }
}

/// Ближайший город с координатами (по умолчанию только major).
City? findNearestCity(
  List<City> cities, {
  required double lat,
  required double lng,
  bool majorOnly = true,
}) {
  City? best;
  var bestKm = double.infinity;
  for (final city in cities) {
    if (majorOnly && !city.isMajor) continue;
    final geo = city.geo;
    if (geo == null) continue;
    final d = _haversineKm(lat, lng, geo.latitude, geo.longitude);
    if (d < bestKm) {
      bestKm = d;
      best = City(
        id: city.id,
        name: city.name,
        slug: city.slug,
        region: city.region,
        geo: city.geo,
        isMajor: city.isMajor,
        sortOrder: city.sortOrder,
        about: city.about,
        distanceM: d * 1000,
      );
    }
  }
  return best;
}

double _haversineKm(double lat1, double lon1, double lat2, double lon2) {
  const r = 6371.0;
  final dLat = _rad(lat2 - lat1);
  final dLon = _rad(lon2 - lon1);
  final a = math.sin(dLat / 2) * math.sin(dLat / 2) +
      math.cos(_rad(lat1)) *
          math.cos(_rad(lat2)) *
          math.sin(dLon / 2) *
          math.sin(dLon / 2);
  return 2 * r * math.asin(math.min(1.0, math.sqrt(a)));
}

double _rad(double deg) => deg * math.pi / 180.0;
