import 'package:city_vibe/features/chat/domain/chat_models.dart';
import 'package:city_vibe/features/chat/presentation/widgets/chat_bubble.dart';
import 'package:flutter/material.dart';

/// Лента сообщений чата с настройками отображения.
///
/// Сейчас — read-only список пузырей. Позже сюда добавим input, pagination,
/// typing indicators и т.д., не меняя экраны-потребители.
class ChatView extends StatelessWidget {
  const ChatView({
    super.key,
    required this.messages,
    required this.currentUserId,
    required this.settings,
    this.padding = const EdgeInsets.fromLTRB(20, 0, 20, 0),
    this.controller,
    this.loading = false,
    this.loadingIndicator,
    this.reverse = false,
  });

  final List<ChatMessage> messages;
  final int currentUserId;
  final ChatDisplaySettings settings;
  final EdgeInsetsGeometry padding;
  final ScrollController? controller;
  final bool loading;
  final Widget? loadingIndicator;
  final bool reverse;

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      controller: controller,
      reverse: reverse,
      padding: padding,
      itemCount: _itemCount,
      itemBuilder: (context, index) {
        if (_showsLoadingIndicator && index == 0) {
          return loadingIndicator ?? _defaultLoadingIndicator();
        }

        final messageIndex = _showsLoadingIndicator ? index - 1 : index;
        final message = messages[messageIndex];
        return ChatBubble(
          key: ValueKey('chat-message-${message.author.id}-$messageIndex'),
          message: message,
          currentUserId: currentUserId,
          settings: settings,
        );
      },
    );
  }

  int get _itemCount => messages.length + (_showsLoadingIndicator ? 1 : 0);

  bool get _showsLoadingIndicator => loading;

  Widget _defaultLoadingIndicator() {
    return const Padding(
      padding: EdgeInsets.only(bottom: 16),
      child: Center(
        child: SizedBox(
          width: 24,
          height: 24,
          child: CircularProgressIndicator(strokeWidth: 2),
        ),
      ),
    );
  }
}
