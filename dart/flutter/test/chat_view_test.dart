import 'package:city_vibe/features/chat/chat.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('ChatView', () {
    const settings = ChatDisplaySettings(
      showAvatars: true,
      showAuthorNames: false,
      showCurrentUserAvatar: true,
    );

    const milana = ChatMessageAuthor(id: 40, name: 'Милана');
    const user = ChatMessageAuthor(id: 7, name: 'Иван');

    testWidgets('renders message bubbles with settings', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ChatView(
              currentUserId: 7,
              settings: settings,
              messages: const [
                ChatMessage(author: milana, text: 'Привет'),
                ChatMessage(author: user, text: 'Ответ'),
              ],
            ),
          ),
        ),
      );

      expect(find.text('Привет'), findsOneWidget);
      expect(find.text('Ответ'), findsOneWidget);
    });

    testWidgets('shows loading header without hiding messages', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ChatView(
              currentUserId: 7,
              settings: settings,
              loading: true,
              messages: const [
                ChatMessage(author: milana, text: 'Привет'),
              ],
            ),
          ),
        ),
      );

      expect(find.byType(CircularProgressIndicator), findsOneWidget);
      expect(find.text('Привет'), findsOneWidget);
    });
  });
}
