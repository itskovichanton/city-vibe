import 'package:city_vibe/core/api/models/catalog_models.dart';
import 'package:city_vibe/features/auth/presentation/widgets/gradient_button.dart';
import 'package:city_vibe/features/onboarding/presentation/widgets/category_chip_wrap.dart';
import 'package:city_vibe/theme/app_colors.dart';
import 'package:flutter/material.dart';

class OnboardingStepThreePage extends StatefulWidget {
  const OnboardingStepThreePage({
    super.key,
    required this.categories,
    required this.initialSelected,
    required this.onContinue,
  });

  final List<CatalogItem> categories;
  final Set<String> initialSelected;
  final Future<void> Function(Set<String> selectedCodes) onContinue;

  @override
  State<OnboardingStepThreePage> createState() => _OnboardingStepThreePageState();
}

class _OnboardingStepThreePageState extends State<OnboardingStepThreePage> {
  late Set<String> _selected;
  bool _submitting = false;

  @override
  void initState() {
    super.initState();
    _selected = Set<String>.from(widget.initialSelected);
  }

  @override
  void didUpdateWidget(OnboardingStepThreePage oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.initialSelected != widget.initialSelected ||
        oldWidget.categories != widget.categories) {
      _selected = Set<String>.from(widget.initialSelected);
    }
  }

  Future<void> _submit() async {
    if (_submitting) return;
    setState(() => _submitting = true);
    try {
      await widget.onContinue(Set<String>.from(_selected));
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return SingleChildScrollView(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            'Вас интересуют эти товары и услуги?',
            style: textTheme.headlineMedium,
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Text(
            'Мы отметили то, что подходит по вашему рассказу. Можно поправить.',
            style: textTheme.bodyMedium?.copyWith(color: AppColors.textSecondary),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 20),
          CategoryChipWrap(
            items: widget.categories
                .map(CategoryChipItem.fromCatalog)
                .toList(growable: false),
            selected: _selected,
            onToggle: (code) {
              setState(() {
                if (_selected.contains(code)) {
                  _selected.remove(code);
                } else {
                  _selected.add(code);
                }
              });
            },
          ),
          const SizedBox(height: 28),
          GradientButton(
            label: _submitting ? 'Сохраняем…' : 'Продолжить',
            onPressed: _submitting ? null : _submit,
          ),
        ],
      ),
    );
  }
}
