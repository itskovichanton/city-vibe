/// Модели справочников (cities и т.п.) по OpenAPI `city-vibe-mobile.json`.
library;

class GeoPoint {
  const GeoPoint({required this.latitude, required this.longitude});

  final double latitude;
  final double longitude;

  factory GeoPoint.fromJson(Map<String, dynamic> json) {
    return GeoPoint(
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
    );
  }

  Map<String, dynamic> toJson() => {
        'latitude': latitude,
        'longitude': longitude,
      };
}

class City {
  const City({
    required this.id,
    required this.name,
    required this.slug,
    this.region = '',
    this.geo,
    this.isMajor = true,
    this.sortOrder = 0,
    this.about = '',
    this.distanceM,
  });

  final int id;
  final String name;
  final String slug;
  final String region;
  final GeoPoint? geo;
  final bool isMajor;
  final int sortOrder;
  final String about;
  final double? distanceM;

  factory City.fromJson(Map<String, dynamic> json) {
    final geoRaw = json['geo'];
    return City(
      id: (json['id'] as num).toInt(),
      name: json['name'] as String,
      slug: json['slug'] as String,
      region: (json['region'] as String?) ?? '',
      geo: geoRaw is Map
          ? GeoPoint.fromJson(Map<String, dynamic>.from(geoRaw))
          : null,
      isMajor: (json['is_major'] as bool?) ?? true,
      sortOrder: (json['sort_order'] as num?)?.toInt() ?? 0,
      about: (json['about'] as String?) ?? '',
      distanceM: (json['distance_m'] as num?)?.toDouble(),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'slug': slug,
        'region': region,
        if (geo != null) 'geo': geo!.toJson(),
        'is_major': isMajor,
        'sort_order': sortOrder,
        'about': about,
        if (distanceM != null) 'distance_m': distanceM,
      };

  @override
  String toString() => 'City($id, $name)';
}
