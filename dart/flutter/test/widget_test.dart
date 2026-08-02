import 'package:city_vibe/app.dart';
import 'package:city_vibe/core/auth/auth_session.dart';
import 'package:city_vibe/core/auth/auth_providers.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class _EmptyAuthStore implements AuthSessionStore {
  @override
  Future<void> clear() async {}

  @override
  Future<AuthSession?> read() async => null;

  @override
  Future<void> write(AuthSession session) async {}
}

void main() {
  testWidgets('приложение показывает экран логина', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authSessionStoreProvider.overrideWithValue(_EmptyAuthStore()),
        ],
        child: const CityVibeApp(),
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('Добро пожаловать!'), findsOneWidget);
    expect(find.text('Войти'), findsOneWidget);
    expect(find.text('CityVibe'), findsOneWidget);
  });
}
