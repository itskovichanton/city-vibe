/// Базовый Dio к api-gateway.
library;

import 'package:city_vibe/core/network/api_config.dart';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:talker_dio_logger/talker_dio_logger.dart';

Dio createDio({String? baseUrl}) {
  final dio = Dio(
    BaseOptions(
      baseUrl: baseUrl ?? ApiConfig.baseUrl,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 60),
      headers: const {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      // Gateway иногда отдаёт бизнес-ошибки не только 4xx — читаем тело сами.
      validateStatus: (status) => status != null && status >= 200 && status < 300,
    ),
  );

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
