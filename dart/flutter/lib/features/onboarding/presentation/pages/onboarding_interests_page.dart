import 'package:city_vibe/core/api/models/catalog_models.dart';
import 'package:city_vibe/features/onboarding/presentation/widgets/category_chip_wrap.dart';
import 'package:city_vibe/theme/app_colors.dart';
import 'package:flutter/material.dart';

/// Выбор чипов справочника с предвыбором от catalog/match.
class OnboardingInterestsPage extends StatefulWidget {
  const OnboardingInterestsPage({
    super.key,
    required this.title,
    required this.subtitle,
    required this.categories,
    required this.initialSelected,
  });

  final String title;
  final String subtitle;
  final List<CatalogItem> categories;
  final Set<String> initialSelected;

  @override
  State<OnboardingInterestsPage> createState() => OnboardingInterestsPageState();
}

class OnboardingInterestsPageState extends State<OnboardingInterestsPage> {
  late Set<String> _selected;

  Set<String> get selected => Set<String>.from(_selected);

  @override
  void initState() {
    super.initState();
    _selected = Set<String>.from(widget.initialSelected);
  }

  @override
  void didUpdateWidget(OnboardingInterestsPage oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.initialSelected != widget.initialSelected ||
        oldWidget.categories != widget.categories) {
      _selected = Set<String>.from(widget.initialSelected);
    }
  }

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return SingleChildScrollView(
      padding: const EdgeInsets.only(bottom: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            widget.title,
            style: textTheme.headlineMedium,
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Text(
            widget.subtitle,
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
        ],
      ),
    );
  }
}
