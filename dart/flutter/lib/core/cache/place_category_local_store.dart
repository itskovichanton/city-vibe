import 'package:city_vibe/core/api/models/place_category.dart';
import 'package:flutter/foundation.dart';
import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';

/// Локальный кэш справочника категорий мест.
abstract class PlaceCategoryLocalStore {
  Future<List<PlaceCategory>> getAll();

  Future<void> replaceAll(List<PlaceCategory> categories);
}

class MemoryPlaceCategoryLocalStore implements PlaceCategoryLocalStore {
  List<PlaceCategory> _items = const [];

  @override
  Future<List<PlaceCategory>> getAll() async => List.unmodifiable(_items);

  @override
  Future<void> replaceAll(List<PlaceCategory> categories) async {
    _items = List.unmodifiable(categories);
  }
}

/// SQLite: `place_categories.db`.
class SqlitePlaceCategoryLocalStore implements PlaceCategoryLocalStore {
  SqlitePlaceCategoryLocalStore({
    DatabaseFactory? databaseFactory,
    String? dbPath,
  })  : _factory = databaseFactory,
        _dbPathOverride = dbPath;

  final DatabaseFactory? _factory;
  final String? _dbPathOverride;
  Database? _db;

  Future<Database> _open() async {
    final existing = _db;
    if (existing != null) return existing;

    final factory = _factory ?? databaseFactory;
    final path = _dbPathOverride ??
        p.join(await getDatabasesPath(), 'place_categories.db');

    final db = await factory.openDatabase(
      path,
      options: OpenDatabaseOptions(
        version: 1,
        onCreate: (db, version) async {
          await db.execute('''
CREATE TABLE place_categories (
  id INTEGER PRIMARY KEY NOT NULL,
  code TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  title_en TEXT NOT NULL DEFAULT '',
  icon_url TEXT,
  sort_order INTEGER NOT NULL DEFAULT 0,
  is_active INTEGER NOT NULL DEFAULT 1
)
''');
        },
      ),
    );
    _db = db;
    return db;
  }

  @override
  Future<List<PlaceCategory>> getAll() async {
    final db = await _open();
    final rows = await db.query(
      'place_categories',
      orderBy: 'sort_order ASC, title ASC',
    );
    return rows.map(_fromRow).toList(growable: false);
  }

  @override
  Future<void> replaceAll(List<PlaceCategory> categories) async {
    final db = await _open();
    final batch = db.batch();
    batch.delete('place_categories');
    for (final category in categories) {
      batch.insert('place_categories', _toRow(category));
    }
    await batch.commit(noResult: true);
  }

  Future<void> close() async {
    final db = _db;
    _db = null;
    await db?.close();
  }

  static Map<String, Object?> _toRow(PlaceCategory category) => {
        'id': category.id,
        'code': category.code,
        'title': category.title,
        'title_en': category.titleEn,
        'icon_url': category.iconUrl,
        'sort_order': category.sortOrder,
        'is_active': category.isActive ? 1 : 0,
      };

  static PlaceCategory _fromRow(Map<String, Object?> row) {
    return PlaceCategory(
      id: (row['id'] as num?)?.toInt() ?? 0,
      code: (row['code'] as String?) ?? '',
      title: (row['title'] as String?) ?? '',
      titleEn: (row['title_en'] as String?) ?? '',
      iconUrl: row['icon_url'] as String?,
      sortOrder: (row['sort_order'] as num?)?.toInt() ?? 0,
      isActive: (row['is_active'] as num?)?.toInt() != 0,
    );
  }
}

PlaceCategoryLocalStore createPlaceCategoryLocalStore() {
  if (kIsWeb) return MemoryPlaceCategoryLocalStore();
  return SqlitePlaceCategoryLocalStore();
}
