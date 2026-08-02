/// Ошибки api-gateway / FastAPI (обёртка `{"error":{message,reason,...}}`).
library;

import 'package:dio/dio.dart';

class ApiException implements Exception {
  ApiException({
    required this.message,
    this.reason,
    this.statusCode,
    this.details,
  });

  /// Человекочитаемое сообщение для UI.
  final String message;

  /// Код причины с бэка: `VALIDATION`, `ERRCODE_...`, `invalid_token`.
  final String? reason;

  final int? statusCode;

  /// Технические детали (traceback и т.п.) — в UI обычно не показываем.
  final String? details;

  bool get isValidation =>
      reason == 'VALIDATION' || statusCode == 422;

  bool get isUnauthorized =>
      statusCode == 401 || reason == 'invalid_token';

  bool get isForbidden => statusCode == 403;

  bool get requiresReLogin => isUnauthorized || isForbidden;

  bool get isNotFound =>
      statusCode == 404 ||
      (reason?.contains('NOT_FOUND') ?? false);

  /// Разбор тела gateway / CoreException presenter.
  factory ApiException.fromResponseData(dynamic data, {int? statusCode}) {
    if (data is Map) {
      final err = data['error'];
      if (err is String) {
        return ApiException(
          message: err,
          reason: err,
          statusCode: statusCode,
        );
      }
      if (err is Map) {
        return ApiException(
          message: (err['message'] as String?)?.trim().isNotEmpty == true
              ? err['message'] as String
              : 'Ошибка сервера',
          reason: err['reason'] as String?,
          details: err['details'] as String?,
          statusCode: statusCode,
        );
      }
      // FastAPI raw: {"detail": ...}
      final detail = data['detail'];
      if (detail is String) {
        return ApiException(message: detail, statusCode: statusCode);
      }
      if (detail is List) {
        return ApiException(
          message: 'Ошибка валидации',
          reason: 'VALIDATION',
          details: detail.toString(),
          statusCode: statusCode ?? 422,
        );
      }
    }
    return ApiException(
      message: 'Неожиданный ответ сервера',
      statusCode: statusCode,
      details: data?.toString(),
    );
  }

  factory ApiException.fromDio(DioException e) {
    final status = e.response?.statusCode;
    final data = e.response?.data;

    if (data != null) {
      return ApiException.fromResponseData(data, statusCode: status);
    }

    switch (e.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
      case DioExceptionType.transformTimeout:
        return ApiException(
          message: 'Сервер не отвечает. Проверьте, что api-gateway запущен.',
          reason: 'TIMEOUT',
          statusCode: status,
        );
      case DioExceptionType.connectionError:
        return ApiException(
          message:
              'Нет связи с api-gateway. Проверьте Wi‑Fi и IP Mac (${e.requestOptions.uri.host}).',
          reason: 'CONNECTION',
          statusCode: status,
        );
      case DioExceptionType.cancel:
        return ApiException(
          message: 'Запрос отменён',
          reason: 'CANCELLED',
          statusCode: status,
        );
      case DioExceptionType.badCertificate:
        return ApiException(
          message: 'Ошибка TLS-сертификата',
          reason: 'TLS',
          statusCode: status,
        );
      case DioExceptionType.badResponse:
        return ApiException(
          message: 'Ошибка сервера (${status ?? '?'})',
          statusCode: status,
        );
      case DioExceptionType.unknown:
        return ApiException(
          message: e.message ?? 'Неизвестная сетевая ошибка',
          statusCode: status,
          details: e.error?.toString(),
        );
    }
  }

  @override
  String toString() =>
      'ApiException($statusCode, reason=$reason, message=$message)';
}
