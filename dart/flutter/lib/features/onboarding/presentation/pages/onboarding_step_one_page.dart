import 'dart:io';

import 'package:cached_network_image/cached_network_image.dart';
import 'package:city_vibe/core/api/models/place_category.dart';
import 'package:city_vibe/core/user/user_providers.dart';
import 'package:city_vibe/features/auth/presentation/widgets/auth_text_field.dart';
import 'package:city_vibe/features/auth/presentation/widgets/gradient_button.dart';
import 'package:city_vibe/theme/app_colors.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

class OnboardingStepOnePage extends ConsumerStatefulWidget {
  const OnboardingStepOnePage({
    super.key,
    required this.categories,
    required this.onContinue,
  });

  final List<PlaceCategory> categories;
  final Future<void> Function({
    required String name,
    required Set<String> selectedCategoryCodes,
    String? avatarFilePath,
  }) onContinue;

  @override
  ConsumerState<OnboardingStepOnePage> createState() =>
      _OnboardingStepOnePageState();
}

class _OnboardingStepOnePageState extends ConsumerState<OnboardingStepOnePage> {
  late final TextEditingController _nameController;
  final _picker = ImagePicker();
  final Set<String> _selected = {};
  String? _avatarFilePath;
  bool _submitting = false;

  @override
  void initState() {
    super.initState();
    final user = ref.read(currentUserProvider).valueOrNull;
    _nameController = TextEditingController(text: user?.name ?? '');
    _selected.addAll(user?.favoriteCategories ?? const []);
    _nameController.addListener(() => setState(() {}));
  }

  @override
  void dispose() {
    _nameController.dispose();
    super.dispose();
  }

  bool get _canContinue =>
      !_submitting &&
      _nameController.text.trim().isNotEmpty &&
      _selected.isNotEmpty;

  Future<void> _pickAvatar() async {
    final file = await _picker.pickImage(
      source: ImageSource.gallery,
      maxWidth: 1200,
      imageQuality: 85,
    );
    if (file == null) return;
    setState(() => _avatarFilePath = file.path);
  }

  Future<void> _submit() async {
    if (!_canContinue) return;
    setState(() => _submitting = true);
    try {
      await widget.onContinue(
        name: _nameController.text.trim(),
        selectedCategoryCodes: Set<String>.from(_selected),
        avatarFilePath: _avatarFilePath,
      );
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  Widget _buildAvatar(String? remoteUrl) {
    if (_avatarFilePath != null) {
      return Image.file(File(_avatarFilePath!), fit: BoxFit.cover);
    }
    if (remoteUrl != null && remoteUrl.isNotEmpty) {
      return CachedNetworkImage(imageUrl: remoteUrl, fit: BoxFit.cover);
    }
    return Icon(
      Icons.camera_alt_outlined,
      size: 32,
      color: AppColors.accent.withValues(alpha: 0.85),
    );
  }

  @override
  Widget build(BuildContext context) {
    final user = ref.watch(currentUserProvider).valueOrNull;
    final textTheme = Theme.of(context).textTheme;

    return SingleChildScrollView(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            'Давайте познакомимся!',
            style: textTheme.headlineMedium,
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Text(
            'Расскажите немного о себе',
            style: textTheme.bodyMedium?.copyWith(color: AppColors.textSecondary),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 24),
          Center(
            child: Column(
              children: [
                GestureDetector(
                  onTap: _pickAvatar,
                  child: Container(
                    width: 96,
                    height: 96,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: AppColors.accent.withValues(alpha: 0.45),
                        width: 2,
                      ),
                      color: AppColors.fieldFill,
                    ),
                    clipBehavior: Clip.antiAlias,
                    child: _buildAvatar(user?.avatarUrl),
                  ),
                ),
                TextButton(
                  onPressed: _pickAvatar,
                  child: const Text('Загрузить фото'),
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),
          AuthTextField(
            controller: _nameController,
            hintText: 'Как к вам обращаться?',
            prefixIcon: Icons.person_outline_rounded,
          ),
          const SizedBox(height: 20),
          Text(
            'Какие места вам нравятся?',
            style: textTheme.titleMedium,
          ),
          const SizedBox(height: 4),
          Text(
            'Выберите любимые категории',
            style: textTheme.bodySmall?.copyWith(color: AppColors.textSecondary),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: widget.categories.map((cat) {
              final selected = _selected.contains(cat.code);
              return FilterChip(
                label: Text(cat.title),
                selected: selected,
                onSelected: (v) {
                  setState(() {
                    if (v) {
                      _selected.add(cat.code);
                    } else {
                      _selected.remove(cat.code);
                    }
                  });
                },
                selectedColor: AppColors.accent.withValues(alpha: 0.35),
                checkmarkColor: AppColors.accent,
                side: BorderSide(
                  color: selected ? AppColors.accent : AppColors.fieldBorder,
                ),
                backgroundColor: AppColors.fieldFill,
                labelStyle: TextStyle(
                  color: selected ? AppColors.textPrimary : AppColors.textSecondary,
                ),
              );
            }).toList(),
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
