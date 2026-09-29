import 'package:city_vibe/core/api/models/catalog_models.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('CatalogItem', () {
    test('fromJson parses product category row', () {
      final item = CatalogItem.fromJson({
        'id': 4,
        'code': 'coffee',
        'title': 'Кофе',
        'title_en': 'Coffee',
        'sort_order': 3,
        'is_active': true,
        'why': 'запрос про кофе',
        'score': 2.5,
        'source': 'both',
      });

      expect(item.id, 4);
      expect(item.code, 'coffee');
      expect(item.title, 'Кофе');
      expect(item.why, 'запрос про кофе');
      expect(item.score, 2.5);
      expect(item.source, 'both');
    });

    test('fromJson falls back to slug/name for cities', () {
      final item = CatalogItem.fromJson({
        'id': 1,
        'slug': 'novosibirsk',
        'name': 'Новосибирск',
        'region': 'НСО',
      });
      expect(item.code, 'novosibirsk');
      expect(item.title, 'Новосибирск');
      expect(item.titleEn, 'НСО');
    });
  });

  group('CatalogMatchResult', () {
    test('fromJson parses match payload', () {
      final result = CatalogMatchResult.fromJson({
        'catalog': 'product_categories',
        'entity_type': 'ProductCategoryInfo',
        'prompt': 'люблю кофе и йогу',
        'fields': ['title'],
        'effort': 50,
        'used_llm': true,
        'items': [
          {'code': 'coffee', 'title': 'Кофе', 'why': 'кофе', 'score': 3.1, 'source': 'llm'},
          {'code': 'yoga_class', 'title': 'Занятие йогой'},
        ],
      });

      expect(result.catalog, 'product_categories');
      expect(result.effort, 50);
      expect(result.usedLlm, isTrue);
      expect(result.items, hasLength(2));
      expect(result.items.first.source, 'llm');
      expect(result.items.first.code, 'coffee');
      expect(result.items.first.why, 'кофе');
      expect(result.items.map((e) => e.code), contains('yoga_class'));
    });
  });

  group('CatalogInfo', () {
    test('fromJson parses registry row', () {
      final info = CatalogInfo.fromJson({
        'catalog': 'product_categories',
        'entity_type': 'ProductCategoryInfo',
        'key_field': 'code',
        'fields': ['title', 'title_en'],
      });
      expect(info.catalog, 'product_categories');
      expect(info.fields, ['title', 'title_en']);
    });
  });
}
