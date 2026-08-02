import 'package:city_vibe/core/api/api_providers.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// После завершения онбординга — показать экран приветствия Миланы один раз.
final milanaWelcomePendingProvider = StateProvider<bool>((ref) => false);

final milanaAccountProvider = FutureProvider((ref) async {
  return ref.watch(milanaClientProvider).getAccount();
});
