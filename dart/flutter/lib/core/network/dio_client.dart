/// Базовый Dio к api-gateway.
library;

import 'package:city_vibe/core/app/app_identity.dart';
import 'package:city_vibe/core/auth/auth_token_coordinator.dart';
import 'package:city_vibe/core/auth/auth_token_holder.dart';
import 'package:city_vibe/core/auth/session_guard.dart';
import 'package:city_vibe/core/network/api_config.dart';
import 'package:city_vibe/core/network/api_exception.dart';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:talker_dio_logger/talker_dio_logger.dart';

/// Маркер повторного запроса после успешного refresh (guard от циклов).
const authRetriedExtraKey = 'auth_retried';

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

/// Bearer JWT — только для защищённых API, не для `/auth/*`.
///
/// Иначе просроченный access блокирует `POST /auth/token/refresh` на gateway
/// (`401 invalid_token` до auth-service).
class _AuthInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final path = options.path;
    if (!path.startsWith('/auth/')) {
      final token = AuthTokenHolder.instance.accessToken;
      if (token != null && token.isNotEmpty) {
        options.headers['Authorization'] = 'Bearer $token';
      }
    }
    handler.next(options);
  }
}

bool _isPublicAuthPath(String path) {
  return path.startsWith('/auth/login') ||
      path.startsWith('/auth/register') ||
      path.contains('/auth/password/');
}

bool _isRefreshEndpoint(String path) {
  return path.startsWith('/auth/token/refresh') ||
      path.startsWith('/auth/logout');
}

ApiException? _apiErrorFrom(DioException err) {
  final status = err.response?.statusCode;
  if (err.response?.data != null) {
    return ApiException.fromResponseData(
      err.response!.data,
      statusCode: status,
    );
  }
  if (status == 401) {
    return ApiException(
      message: SessionGuard.messageForAuthHttpError(
        ApiException(statusCode: 401, message: ''),
      ),
      statusCode: 401,
    );
  }
  return null;
}

void _logoutAfterAuthFailure(DioException err) {
  SessionGuard.instance.handleUnauthorized(_apiErrorFrom(err));
}

/// Единственное место для 401: refresh → retry или logout.
///
/// [QueuedInterceptor] сериализует параллельные 401 (один refresh на пачку запросов).
class _AuthRecoveryInterceptor extends QueuedInterceptor {
  _AuthRecoveryInterceptor(this._dio);

  final Dio _dio;

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    final status = err.response?.statusCode;
    if (status != 401) {
      handler.next(err);
      return;
    }

    final request = err.requestOptions;
    final path = request.path;

    if (_isRefreshEndpoint(path)) {
      _logoutAfterAuthFailure(err);
      handler.next(err);
      return;
    }

    if (_isPublicAuthPath(path)) {
      handler.next(err);
      return;
    }

    if (request.extra[authRetriedExtraKey] == true) {
      _logoutAfterAuthFailure(err);
      handler.next(err);
      return;
    }

    final tryRefresh = AuthTokenCoordinator.instance.tryRefreshSession;
    if (tryRefresh == null) {
      _logoutAfterAuthFailure(err);
      handler.next(err);
      return;
    }

    final refreshed = await tryRefresh();
    if (!refreshed) {
      _logoutAfterAuthFailure(err);
      handler.next(err);
      return;
    }

    try {
      request.extra[authRetriedExtraKey] = true;
      final token = AuthTokenHolder.instance.accessToken;
      if (token != null && token.isNotEmpty) {
        request.headers['Authorization'] = 'Bearer $token';
      }
      final response = await _dio.fetch<dynamic>(request);
      handler.resolve(response);
    } catch (_) {
      _logoutAfterAuthFailure(err);
      handler.next(err);
    }
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
      validateStatus: (status) => status != null && status >= 200 && status < 300,
    ),
  );

  dio.interceptors.add(_UserAgentInterceptor(ua));
  dio.interceptors.add(_AuthInterceptor());
  dio.interceptors.add(_AuthRecoveryInterceptor(dio));

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
