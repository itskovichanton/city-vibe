import 'package:city_vibe/core/api/api_providers.dart';
import 'package:city_vibe/core/milana/milana_local_store.dart';
import 'package:city_vibe/core/milana/milana_repository.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final milanaLocalStoreProvider = FutureProvider<MilanaLocalStore>((ref) async {
  return createMilanaLocalStore();
});

final milanaRepositoryProvider = FutureProvider<MilanaRepository>((ref) async {
  final store = await ref.watch(milanaLocalStoreProvider.future);
  return MilanaRepository(
    client: ref.watch(milanaClientProvider),
    store: store,
    dio: ref.watch(dioProvider),
  );
});
