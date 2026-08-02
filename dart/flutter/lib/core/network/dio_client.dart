/// Базовый Dio к api-gateway.
library;

import 'package:city_vibe/core/app/app_identity.dart';
import 'package:city_vibe/core/auth/auth_token_holder.dart';
import 'package:city_vibe/core/auth/session_guard.dart';
import 'package:city_vibe/core/network/api_config.dart';
import 'package:city_vibe/core/network/api_exception.dart';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:talker_dio_logger/talker_dio_logger.dart';

/// Interceptor: гарантирует User-Agent на каждом запросе (в т.ч. FormData).
class _UserAgentInterceptor extends Interceptor {
  _UserAgentInterceptor(this.userAgent);

  final String userAgent;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    options.headers['User-Agent'] = userAgent;
    handler.next(options);
  }
}

/// Bearer JWT из [AuthTokenHolder] (обновляется при login/logout).
class _AuthInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final token = AuthTokenHolder.instance.accessToken;
    if (token != null && token.isNotEmpty) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }
}

/// 401/403 → принудительный выход с toast (см. [SessionGuard]).
class _SessionErrorInterceptor extends Interceptor {
  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    final status = err.response?.statusCode;
    if (status == 401 || status == 403) {
      final apiError = err.response?.data != null
          ? ApiException.fromResponseData(
              err.response!.data,
              statusCode: status,
            )
          : ApiException(
              message: SessionGuard.messageForAuthHttpError(
                ApiException(statusCode: status, message: ''),
              ),
              statusCode: status,
            );
      SessionGuard.instance.handleAuthHttpError(apiError);
    }
    handler.next(err);
  }
}

Dio createDio({String? baseUrl, String? userAgent}) {
  final ua = userAgent ?? AppIdentity.userAgentValue;
  final dio = Dio(
    BaseOptions(
      baseUrl: baseUrl ?? ApiConfig.baseUrl,
      connectTimeout: ApiConfig.httpTimeout,
      receiveTimeout: ApiConfig.httpTimeout,
      sendTimeout: ApiConfig.httpTimeout,
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': ua,
      },
      // Gateway иногда отдаёт бизнес-ошибки не только 4xx — читаем тело сами.
      validateStatus: (status) => status != null && status >= 200 && status < 300,
    ),
  );

  dio.interceptors.add(_UserAgentInterceptor(ua));
  dio.interceptors.add(_AuthInterceptor());
  dio.interceptors.add(_SessionErrorInterceptor());

  if (kDebugMode) {
    dio.interceptors.add(
      TalkerDioLogger(
        settings: const TalkerDioLoggerSettings(
          printRequestHeaders: false,
          printResponseHeaders: false,
          printResponseMessage: true,
        ),
      ),
    );
  }

  return dio;
}
