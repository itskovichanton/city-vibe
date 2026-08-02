import 'package:city_vibe/core/milana/milana_providers.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

export 'milana_welcome_pending.dart';

final milanaAccountProvider = FutureProvider((ref) async {
  final repo = await ref.watch(milanaRepositoryProvider.future);
  return repo.loadAccount();
});
