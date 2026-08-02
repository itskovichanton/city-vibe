import 'package:city_vibe/core/network/api_config.dart';

/// S3-ключ из API → URL загрузки через gateway (`GET /media/...`).
abstract final class MediaUrlResolver {
  static const mediaPathPrefix = '/media/';

  /// [storageRef] — S3-ключ (`avatars/45/uuid.jpg`) или legacy full URL из старых записей.
  static String? resolve(String? storageRef) {
    if (storageRef == null || storageRef.isEmpty) return null;

    if (storageRef.startsWith('http://') || storageRef.startsWith('https://')) {
      final uri = Uri.tryParse(storageRef);
      if (uri != null &&
          uri.host != 'localhost' &&
          uri.host != '127.0.0.1') {
        return storageRef;
      }
    }

    final key = _extractStorageKey(storageRef);
    if (key == null || key.isEmpty) return null;

    final base = ApiConfig.baseUrl.replaceAll(RegExp(r'/+$'), '');
    return '$base$mediaPathPrefix$key';
  }

  static String? _extractStorageKey(String ref) {
    if (ref.startsWith('http://') || ref.startsWith('https://')) {
      final uri = Uri.tryParse(ref);
      if (uri == null) return null;
      final path = uri.path.replaceFirst(RegExp(r'^/+'), '');
      const bucketPrefix = 'city-vibe/';
      if (path.startsWith(bucketPrefix)) {
        return path.substring(bucketPrefix.length);
      }
      return path;
    }
    return ref.replaceFirst(RegExp(r'^/+'), '');
  }
}
