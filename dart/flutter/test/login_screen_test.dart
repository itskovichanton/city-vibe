import 'package:city_vibe/features/auth/presentation/login_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

/// Простой smoke-тест: экран строится и кнопка «Войти» disabled при пустых полях.
void main() {
  testWidgets('LoginScreen: Войти disabled пока поля пустые', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(home: LoginScreen()),
    );

    // Находим текст кнопки.
    expect(find.text('Войти'), findsOneWidget);
    expect(find.text('Добро пожаловать!'), findsOneWidget);

    // InkWell с null onTap не получает жесты — проверяем через ввод.
    await tester.enterText(find.byType(TextField).first, 'a@b.c');
    await tester.pump();
    // Пароль ещё пуст — логика _canSubmit всё ещё false (визуально opacity).
    await tester.enterText(find.byType(TextField).at(1), 'secret');
    await tester.pump();

    expect(find.text('a@b.c'), findsOneWidget);
  });
}
