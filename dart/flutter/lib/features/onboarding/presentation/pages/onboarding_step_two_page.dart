import 'package:city_vibe/core/user/user_providers.dart';
import 'package:city_vibe/features/auth/presentation/widgets/gradient_button.dart';
import 'package:city_vibe/theme/app_colors.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class OnboardingStepTwoPage extends ConsumerStatefulWidget {
  const OnboardingStepTwoPage({
    super.key,
    required this.onContinue,
  });

  final Future<void> Function(String longBio) onContinue;

  @override
  ConsumerState<OnboardingStepTwoPage> createState() =>
      _OnboardingStepTwoPageState();
}

class _OnboardingStepTwoPageState extends ConsumerState<OnboardingStepTwoPage> {
  static const _maxLen = 500;
  late final TextEditingController _bioController;
  bool _submitting = false;

  @override
  void initState() {
    super.initState();
    final user = ref.read(currentUserProvider).valueOrNull;
    _bioController = TextEditingController(text: user?.longBio ?? '');
    _bioController.addListener(() => setState(() {}));
  }

  @override
  void dispose() {
    _bioController.dispose();
    super.dispose();
  }

  bool get _canContinue => !_submitting && _bioController.text.trim().isNotEmpty;

  Future<void> _submit() async {
    if (!_canContinue) return;
    setState(() => _submitting = true);
    try {
      await widget.onContinue(_bioController.text.trim());
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    final len = _bioController.text.length;

    return SingleChildScrollView(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            'Расскажите о себе',
            style: textTheme.headlineMedium,
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Text(
            'Напишите в свободной форме',
            style: textTheme.bodyMedium?.copyWith(color: AppColors.textSecondary),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 24),
          TextField(
            controller: _bioController,
            maxLines: 8,
            maxLength: _maxLen,
            style: textTheme.bodyMedium,
            decoration: InputDecoration(
              hintText:
                  'Я обожаю атмосферные места, парки, у меня есть машина, …',
              hintStyle: textTheme.bodyMedium?.copyWith(
                color: AppColors.textSecondary.withValues(alpha: 0.7),
              ),
              filled: true,
              fillColor: AppColors.fieldFill,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(16),
                borderSide: const BorderSide(color: AppColors.fieldBorder),
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(16),
                borderSide: const BorderSide(color: AppColors.fieldBorder),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(16),
                borderSide: const BorderSide(color: AppColors.accent, width: 1.5),
              ),
              counterText: '$len/$_maxLen',
            ),
          ),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppColors.accent.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: AppColors.accent.withValues(alpha: 0.25)),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.auto_awesome, color: AppColors.accent, size: 20),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    'Чем больше Вы расскажете о себе, тем точнее ИИ-Ассистент Милана '
                    'подберёт места и события под Ваши интересы.',
                    style: textTheme.bodySmall,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 28),
          GradientButton(
            label: _submitting ? 'Сохраняем…' : 'Продолжить',
            onPressed: _canContinue ? _submit : null,
          ),
        ],
      ),
    );
  }
}
