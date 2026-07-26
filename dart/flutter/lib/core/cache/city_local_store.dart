import 'package:city_vibe/core/api/models/city.dart';
import 'package:flutter/foundation.dart';
import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';

/// Локальный кэш городов (SQLite на устройстве; на web — in-memory).
abstract class CityLocalStore {
  Future<List<City>> getAll();

  Future<void> replaceAll(List<City> cities);
}

/// In-memory fallback (web / тесты).
class MemoryCityLocalStore implements CityLocalStore {
  List<City> _cities = const [];

  @override
  Future<List<City>> getAll() async => List.unmodifiable(_cities);

  @override
  Future<void> replaceAll(List<City> cities) async {
    _cities = List.unmodifiable(cities);
  }
}

/// SQLite: `city_vibe.db` → таблица `cities`.
class SqliteCityLocalStore implements CityLocalStore {
  SqliteCityLocalStore({DatabaseFactory? databaseFactory, String? dbPath})
      : _factory = databaseFactory,
        _dbPathOverride = dbPath;

  final DatabaseFactory? _factory;
  final String? _dbPathOverride;
  Database? _db;

  Future<Database> _open() async {
    final existing = _db;
    if (existing != null) return existing;

    final factory = _factory ?? databaseFactory;
    final path = _dbPathOverride ??
        p.join(await getDatabasesPath(), 'city_vibe.db');

    final db = await factory.openDatabase(
      path,
      options: OpenDatabaseOptions(
        version: 1,
        onCreate: (db, version) async {
          await db.execute('''
CREATE TABLE cities (
  id INTEGER PRIMARY KEY NOT NULL,
  name TEXT NOT NULL,
  slug TEXT NOT NULL,
  region TEXT NOT NULL DEFAULT '',
  latitude REAL,
  longitude REAL,
  is_major INTEGER NOT NULL DEFAULT 1,
  sort_order INTEGER NOT NULL DEFAULT 0,
  about TEXT NOT NULL DEFAULT ''
)
''');
          await db.execute('''
CREATE TABLE cache_meta (
  key TEXT PRIMARY KEY NOT NULL,
  value TEXT NOT NULL
)
''');
        },
      ),
    );
    _db = db;
    return db;
  }

  @override
  Future<List<City>> getAll() async {
    final db = await _open();
    final rows = await db.query(
      'cities',
      orderBy: 'sort_order ASC, name ASC',
    );
    return rows.map(_fromRow).toList(growable: false);
  }

  @override
  Future<void> replaceAll(List<City> cities) async {
    final db = await _open();
    final batch = db.batch();
    batch.delete('cities');
    for (final city in cities) {
      batch.insert('cities', _toRow(city));
    }
    batch.insert(
      'cache_meta',
      {
        'key': 'cities_fetched_at',
        'value': DateTime.now().toUtc().toIso8601String(),
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
    await batch.commit(noResult: true);
  }

  Future<void> close() async {
    final db = _db;
    _db = null;
    await db?.close();
  }

  static Map<String, Object?> _toRow(City city) => {
        'id': city.id,
        'name': city.name,
        'slug': city.slug,
        'region': city.region,
        'latitude': city.geo?.latitude,
        'longitude': city.geo?.longitude,
        'is_major': city.isMajor ? 1 : 0,
        'sort_order': city.sortOrder,
        'about': city.about,
      };

  static City _fromRow(Map<String, Object?> row) {
    final lat = row['latitude'] as num?;
    final lng = row['longitude'] as num?;
    return City(
      id: row['id'] as int,
      name: row['name'] as String,
      slug: row['slug'] as String,
      region: (row['region'] as String?) ?? '',
      geo: lat != null && lng != null
          ? GeoPoint(latitude: lat.toDouble(), longitude: lng.toDouble())
          : null,
      isMajor: (row['is_major'] as int? ?? 1) == 1,
      sortOrder: (row['sort_order'] as int?) ?? 0,
      about: (row['about'] as String?) ?? '',
    );
  }
}

/// Фабрика store: SQLite на мобилках/десктопе, memory на web.
CityLocalStore createCityLocalStore() {
  if (kIsWeb) return MemoryCityLocalStore();
  return SqliteCityLocalStore();
}
