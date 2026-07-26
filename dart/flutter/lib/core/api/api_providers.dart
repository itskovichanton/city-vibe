import 'dart:async';

import 'package:city_vibe/core/api/auth_client.dart';
import 'package:city_vibe/core/api/common_client.dart';
import 'package:city_vibe/core/api/user_client.dart';
import 'package:city_vibe/core/cache/cities_repository.dart';
import 'package:city_vibe/core/cache/city_local_store.dart';
import 'package:city_vibe/core/network/api_http.dart';
import 'package:city_vibe/core/network/dio_client.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final dioProvider = Provider<Dio>((ref) {
  final dio = createDio();
  ref.onDispose(dio.close);
  return dio;
});

final apiHttpProvider = Provider<ApiHttp>((ref) {
  return ApiHttp(ref.watch(dioProvider));
});

final commonClientProvider = Provider<CommonClient>((ref) {
  return CommonClient(ref.watch(apiHttpProvider));
});

final authClientProvider = Provider<AuthClient>((ref) {
  return AuthClient(ref.watch(apiHttpProvider));
});

final userClientProvider = Provider<UserClient>((ref) {
  return UserClient(ref.watch(apiHttpProvider));
});

final cityLocalStoreProvider = Provider<CityLocalStore>((ref) {
  final store = createCityLocalStore();
  ref.onDispose(() {
    final s = store;
    if (s is SqliteCityLocalStore) {
      unawaited(s.close());
    }
  });
  return store;
});

final citiesRepositoryProvider = Provider<CitiesRepository>((ref) {
  return CitiesRepository(
    client: ref.watch(commonClientProvider),
    store: ref.watch(cityLocalStoreProvider),
  );
});
