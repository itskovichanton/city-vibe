import 'package:city_vibe/core/api/models/catalog_models.dart';
import 'package:city_vibe/features/onboarding/presentation/pages/onboarding_interests_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('OnboardingInterestsPage shows title and keeps preselected chips',
      (tester) async {
    Set<String>? submitted;

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: OnboardingInterestsPage(
            title: 'Вам интересны эти места вокруг вас?',
            subtitle: 'Можно поправить',
            categories: const [
              CatalogItem(code: 'cafes', title: 'Кафе'),
              CatalogItem(code: 'parks', title: 'Парки'),
            ],
            initialSelected: const {'cafes'},
            onContinue: (selected) async {
              submitted = selected;
            },
          ),
        ),
      ),
    );

    expect(find.text('Вам интересны эти места вокруг вас?'), findsOneWidget);
    expect(find.text('Кафе'), findsOneWidget);
    expect(find.text('Парки'), findsOneWidget);

    await tester.tap(find.text('Продолжить'));
    await tester.pump();
    expect(submitted, {'cafes'});
  });
}
