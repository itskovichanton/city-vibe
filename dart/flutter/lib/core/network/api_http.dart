/// Тонкий HTTP-слой поверх Dio: только transport + разбор `{result}` / `{error}`.
///
/// Доменные клиенты ([AuthClient], [UserClient], [CommonClient]) не трогают Dio.
library;

import 'package:city_vibe/core/network/api_exception.dart';
import 'package:dio/dio.dart';

typedef JsonMap = Map<String, dynamic>;

class ApiHttp {
  ApiHttp(this._dio);

  final Dio _dio;

  Future<T> get<T>(
    String path, {
    Map<String, dynamic>? query,
    required T Function(dynamic data) parse,
  }) {
    return _send(
      () => _dio.get<dynamic>(path, queryParameters: query),
      parse: parse,
    );
  }

  Future<T> post<T>(
    String path, {
    Object? body,
    required T Function(dynamic data) parse,
  }) {
    return _send(
      () => _dio.post<dynamic>(path, data: body),
      parse: parse,
    );
  }

  Future<T> put<T>(
    String path, {
    Object? body,
    required T Function(dynamic data) parse,
  }) {
    return _send(
      () => _dio.put<dynamic>(path, data: body),
      parse: parse,
    );
  }

  Future<T> patch<T>(
    String path, {
    Object? body,
    required T Function(dynamic data) parse,
  }) {
    return _send(
      () => _dio.patch<dynamic>(path, data: body),
      parse: parse,
    );
  }

  Future<T> delete<T>(
    String path, {
    Object? body,
    required T Function(dynamic data) parse,
  }) {
    return _send(
      () => _dio.delete<dynamic>(path, data: body),
      parse: parse,
    );
  }

  /// Все сетевые вызовы — async (IO не блокирует UI-isolate).
  Future<T> _send<T>(
    Future<Response<dynamic>> Function() call, {
    required T Function(dynamic data) parse,
  }) async {
    try {
      final response = await call();
      final payload = _unwrapPayload(response.data, response.statusCode);
      return parse(payload);
    } on ApiException {
      rethrow;
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    } catch (e) {
      throw ApiException(message: e.toString(), reason: 'CLIENT');
    }
  }

  /// Успех: `{ "result": ... }` или «сырое» тело.
  /// Ошибка в 200 с `error` — тоже бросаем (на всякий случай).
  dynamic _unwrapPayload(dynamic data, int? statusCode) {
    if (data is Map) {
      if (data.containsKey('error') && data['error'] != null) {
        throw ApiException.fromResponseData(data, statusCode: statusCode);
      }
      if (data.containsKey('result')) {
        return data['result'];
      }
    }
    return data;
  }
}
