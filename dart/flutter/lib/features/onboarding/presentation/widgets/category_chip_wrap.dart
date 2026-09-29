import 'package:city_vibe/core/api/models/catalog_models.dart';
import 'package:city_vibe/core/api/models/place_category.dart';
import 'package:city_vibe/theme/app_colors.dart';
import 'package:flutter/material.dart';

class CategoryChipItem {
  const CategoryChipItem({required this.code, required this.title});

  final String code;
  final String title;

  factory CategoryChipItem.fromPlace(PlaceCategory category) {
    return CategoryChipItem(code: category.code, title: category.title);
  }

  factory CategoryChipItem.fromCatalog(CatalogItem item) {
    return CategoryChipItem(code: item.code, title: item.title);
  }
}

class CategoryChipWrap extends StatelessWidget {
  const CategoryChipWrap({
    super.key,
    required this.items,
    required this.selected,
    required this.onToggle,
  });

  final List<CategoryChipItem> items;
  final Set<String> selected;
  final ValueChanged<String> onToggle;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: items.map((item) {
        final isSelected = selected.contains(item.code);
        return FilterChip(
          label: Text(item.title),
          selected: isSelected,
          showCheckmark: false,
          onSelected: (_) => onToggle(item.code),
          selectedColor: AppColors.accent.withValues(alpha: 0.35),
          side: BorderSide(
            color: isSelected ? AppColors.accent : AppColors.fieldBorder,
          ),
          backgroundColor: AppColors.fieldFill,
          labelStyle: TextStyle(
            color: isSelected ? AppColors.textPrimary : AppColors.textSecondary,
          ),
        );
      }).toList(growable: false),
    );
  }
}
