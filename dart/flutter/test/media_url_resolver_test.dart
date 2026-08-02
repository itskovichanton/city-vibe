import 'package:city_vibe/core/network/api_config.dart';
import 'package:city_vibe/core/network/media_url_resolver.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('resolve builds gateway media URL from storage key', () {
    const key = 'avatars/45/e11bc051f46a4e24929e29d3879911ed.jpg';
    final url = MediaUrlResolver.resolve(key)!;
    expect(url, '${ApiConfig.baseUrl}${MediaUrlResolver.mediaPathPrefix}$key');
    expect(url, isNot(contains('localhost:9000')));
  });

  test('resolve extracts key from legacy MinIO URL', () {
    const legacy =
        'http://localhost:9000/city-vibe/avatars/45/e11bc051.jpg';
    final url = MediaUrlResolver.resolve(legacy)!;
    expect(
      url,
      '${ApiConfig.baseUrl}/media/avatars/45/e11bc051.jpg',
    );
  });

  test('resolve passes through external CDN URLs', () {
    const url = 'https://cdn.example.com/avatars/u.jpg';
    expect(MediaUrlResolver.resolve(url), url);
  });
}
