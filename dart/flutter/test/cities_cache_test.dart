import 'package:city_vibe/core/api/models/city.dart';
import 'package:city_vibe/core/cache/cities_repository.dart';
import 'package:city_vibe/core/cache/city_local_store.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('MemoryCityLocalStore', () {
    test('replaceAll / getAll round-trip', () async {
      final store = MemoryCityLocalStore();
      expect(await store.getAll(), isEmpty);

      await store.replaceAll([
        const City(
          id: 1,
          name: 'Москва',
          slug: 'moskva',
          region: 'Москва',
          geo: GeoPoint(latitude: 55.75, longitude: 37.62),
          sortOrder: 1,
        ),
        const City(
          id: 3,
          name: 'Новосибирск',
          slug: 'novosibirsk',
          region: 'НСО',
          geo: GeoPoint(latitude: 55.03, longitude: 82.92),
          sortOrder: 3,
        ),
      ]);

      final all = await store.getAll();
      expect(all, hasLength(2));
      expect(all.first.name, 'Москва');
      expect(all.last.geo?.latitude, 55.03);
    });
  });

  group('findNearestCity', () {
    const cities = [
      City(
        id: 1,
        name: 'Москва',
        slug: 'moskva',
        geo: GeoPoint(latitude: 55.7558, longitude: 37.6173),
      ),
      City(
        id: 3,
        name: 'Новосибирск',
        slug: 'novosibirsk',
        geo: GeoPoint(latitude: 55.0084, longitude: 82.9357),
      ),
    ];

    test('picks nearest by haversine', () {
      // Точка рядом с Новосибирском
      final nearest = findNearestCity(
        cities,
        lat: 55.02,
        lng: 82.90,
      );
      expect(nearest?.id, 3);
      expect(nearest?.distanceM, isNotNull);
      expect(nearest!.distanceM!, lessThan(50000));
    });

    test('returns null when no geo', () {
      expect(
        findNearestCity(
          const [City(id: 9, name: 'X', slug: 'x')],
          lat: 1,
          lng: 2,
        ),
        isNull,
      );
    });
  });
}
