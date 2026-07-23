/// Базовый Dio-клиент к api-gateway.
///
/// Пока без реального API: готовим инфраструктуру.
/// Позже: interceptors (JWT), baseUrl из конфига, Riverpod-провайдер.
library;

import 'package:dio/dio.dart';
import 'package:talker_dio_logger/talker_dio_logger.dart';

/// Создаёт настроенный [Dio].
///
/// [baseUrl] на Android-эмуляторе к хост-машине: `http://10.0.2.2:8080`
/// на реальном телефоне: `http://<IP-твоего-Mac-в-LAN>:8080`
/// на Chrome/desktop: `http://127.0.0.1:8080`
Dio createDio({String baseUrl = 'http://127.0.0.1:8080'}) {
  final dio = Dio(
    BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 60),
      headers: const {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
    ),
  );

  // Логи запросов/ответов в debug — удобно учиться и отлаживать.
  dio.interceptors.add(
    TalkerDioLogger(
      settings: const TalkerDioLoggerSettings(
        printRequestHeaders: true,
        printResponseHeaders: false,
        printResponseMessage: true,
      ),
    ),
  );

  return dio;
}
