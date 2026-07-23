import 'package:city_vibe/app.dart';
import 'package:flutter_test/flutter_test.dart';

/// Smoke: приложение стартует на LoginScreen.
void main() {
  testWidgets('CityVibeApp показывает экран логина', (tester) async {
    await tester.pumpWidget(const CityVibeApp());
    // google_fonts может дергать сеть — даём кадр(ы).
    await tester.pump();

    expect(find.text('Добро пожаловать!'), findsOneWidget);
    expect(find.text('Войти'), findsOneWidget);
    expect(find.text('CityVibe'), findsOneWidget);
  });
}
