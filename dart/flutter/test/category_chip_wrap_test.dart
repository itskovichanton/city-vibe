import 'package:city_vibe/features/onboarding/presentation/widgets/category_chip_wrap.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('CategoryChipWrap toggles selection', (tester) async {
    final selected = <String>{'coffee'};

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: StatefulBuilder(
            builder: (context, setState) {
              return CategoryChipWrap(
                items: const [
                  CategoryChipItem(code: 'coffee', title: 'Кофе'),
                  CategoryChipItem(code: 'yoga_class', title: 'Йога'),
                ],
                selected: selected,
                onToggle: (code) {
                  setState(() {
                    if (selected.contains(code)) {
                      selected.remove(code);
                    } else {
                      selected.add(code);
                    }
                  });
                },
              );
            },
          ),
        ),
      ),
    );

    expect(find.text('Кофе'), findsOneWidget);
    expect(find.text('Йога'), findsOneWidget);

    await tester.tap(find.text('Йога'));
    await tester.pump();
    expect(selected, containsAll(['coffee', 'yoga_class']));

    await tester.tap(find.text('Кофе'));
    await tester.pump();
    expect(selected, {'yoga_class'});
  });
}
