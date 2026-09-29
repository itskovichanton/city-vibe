import 'dart:async';

import 'package:city_vibe/core/api/catalog_client.dart';
import 'package:city_vibe/core/api/models/place_category.dart';
import 'package:city_vibe/core/cache/place_category_local_store.dart';

/// Категории мест: cache-first, сеть обновляет кэш в фоне.
class PlaceCategoriesRepository {
  PlaceCategoriesRepository({
    required CatalogClient client,
    required PlaceCategoryLocalStore store,
  })  : _client = client,
        _store = store;

  final CatalogClient _client;
  final PlaceCategoryLocalStore _store;

  Future<void>? _refreshInFlight;

  /// Если кэш не пуст — сразу его, сеть — тихо.
  /// Если пуст — ждём сеть.
  Future<List<PlaceCategory>> getAll({bool forceRefresh = false}) async {
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

  Future<void> _refreshFromNetwork() {
    final inFlight = _refreshInFlight;
    if (inFlight != null) return inFlight;
    final future = () async {
      try {
        await _fetchAndCache();
      } catch (_) {
        // Офлайн / 5xx — оставляем старый кэш.
      }
    }()
        .whenComplete(() {
      _refreshInFlight = null;
    });
    _refreshInFlight = future;
    return future;
  }

  Future<List<PlaceCategory>> _fetchAndCache() async {
    final fresh = await _client.getPlaceCategories();
    final mapped =
        fresh.map(PlaceCategory.fromCatalogItem).toList(growable: false);
    await _store.replaceAll(mapped);
    return mapped;
  }
}
