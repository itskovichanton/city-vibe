import 'package:city_vibe/core/api/models/place_category.dart';
import 'package:city_vibe/core/api/models/user_models.dart';
import 'package:city_vibe/core/milana/milana_account.dart';
import 'package:city_vibe/core/user/user_providers.dart';
import 'package:city_vibe/features/home/home_providers.dart';
import 'package:city_vibe/features/home/presentation/home_screen.dart';
import 'package:city_vibe/features/onboarding/onboarding_providers.dart';
import 'package:city_vibe/theme/app_theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

class _FixedUserNotifier extends CurrentUserNotifier {
  _FixedUserNotifier(this._user);

  final UserProfile _user;

  @override
  Future<UserProfile?> build() async => _user;
}

void main() {
  testWidgets('HomeScreen shows favorite place categories and lets select one',
      (tester) async {
    const user = UserProfile(
      id: 1,
      name: 'Антон',
      favoriteCategories: ['bars', 'cafes'],
      onboardingCompleted: true,
    );
    const milana = MilanaAccount(
      profile: UserProfile(id: 0, name: 'Милана', role: 'MILANA'),
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          currentUserProvider.overrideWith(() => _FixedUserNotifier(user)),
          placeCategoriesProvider.overrideWith(
            (ref) async => const [
              PlaceCategory(id: 1, code: 'bars', title: 'Бары'),
              PlaceCategory(id: 2, code: 'cafes', title: 'Кафе'),
              PlaceCategory(id: 3, code: 'parks', title: 'Парки'),
            ],
          ),
          milanaAccountProvider.overrideWith((ref) async => milana),
        ],
        child: MaterialApp(
          theme: buildAppTheme(),
          home: const HomeScreen(),
        ),
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 50));

    expect(find.text('Все места'), findsOneWidget);
    expect(find.text('Бары'), findsOneWidget);
    expect(find.text('Кафе'), findsOneWidget);
    expect(find.text('Парки'), findsNothing);
    expect(find.text('Милана'), findsOneWidget);
    expect(find.text('Ёмкость'), findsWidgets);
    expect(find.text('Карта'), findsOneWidget);
    expect(find.byType(DraggableScrollableSheet), findsOneWidget);

    final element = tester.element(find.byType(HomeScreen));
    final container = ProviderScope.containerOf(element);
    expect(container.read(selectedHomeCategoryCodeProvider), 'all_places');

    await tester.tap(find.text('Бары'));
    await tester.pump();
    expect(container.read(selectedHomeCategoryCodeProvider), 'bars');
  });
}
