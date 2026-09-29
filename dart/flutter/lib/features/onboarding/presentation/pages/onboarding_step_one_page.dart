import 'dart:io';

import 'package:cached_network_image/cached_network_image.dart';
import 'package:city_vibe/core/user/user_providers.dart';
import 'package:city_vibe/features/auth/presentation/widgets/auth_text_field.dart';
import 'package:city_vibe/theme/app_colors.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

class OnboardingStepOnePage extends ConsumerStatefulWidget {
  const OnboardingStepOnePage({
    super.key,
    required this.onContinue,
    this.onChanged,
  });

  final Future<void> Function({
    required String name,
    required String longBio,
    String? avatarFilePath,
  }) onContinue;
  final VoidCallback? onChanged;

  @override
  ConsumerState<OnboardingStepOnePage> createState() =>
      OnboardingStepOnePageState();
}

class OnboardingStepOnePageState extends ConsumerState<OnboardingStepOnePage> {
  static const _bioMaxLen = 500;
  late final TextEditingController _nameController;
  late final TextEditingController _bioController;
  final _picker = ImagePicker();
  String? _avatarFilePath;

  bool get canContinue =>
      _nameController.text.trim().isNotEmpty &&
      _bioController.text.trim().isNotEmpty;

  @override
  void initState() {
    super.initState();
    final user = ref.read(currentUserProvider).valueOrNull;
    _nameController = TextEditingController(text: user?.name ?? '');
    _bioController = TextEditingController(text: user?.longBio ?? '');
    _nameController.addListener(_onFieldsChanged);
    _bioController.addListener(_onFieldsChanged);
    WidgetsBinding.instance.addPostFrameCallback((_) => widget.onChanged?.call());
  }

  void _onFieldsChanged() {
    setState(() {});
    widget.onChanged?.call();
  }

  @override
  void dispose() {
    _nameController.dispose();
    _bioController.dispose();
    super.dispose();
  }

  Future<void> submit() async {
    if (!canContinue) return;
    await widget.onContinue(
      name: _nameController.text.trim(),
      longBio: _bioController.text.trim(),
      avatarFilePath: _avatarFilePath,
    );
  }

  Future<void> _pickAvatar() async {
    final source = await showModalBottomSheet<ImageSource>(
      context: context,
      backgroundColor: AppColors.backgroundDeep,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return SafeArea(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Padding(
                padding: EdgeInsets.fromLTRB(20, 16, 20, 8),
                child: Text(
                  'Фото профиля',
                  style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 18,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              ListTile(
                leading: const Icon(
                  Icons.photo_camera_outlined,
                  color: AppColors.accent,
                ),
                title: const Text(
                  'Сделать фото',
                  style: TextStyle(color: AppColors.textPrimary),
                ),
                onTap: () => Navigator.pop(context, ImageSource.camera),
              ),
              ListTile(
                leading: const Icon(
                  Icons.photo_library_outlined,
                  color: AppColors.accent,
                ),
                title: const Text(
                  'Выбрать из галереи',
                  style: TextStyle(color: AppColors.textPrimary),
                ),
                onTap: () => Navigator.pop(context, ImageSource.gallery),
              ),
              const SizedBox(height: 8),
            ],
          ),
        );
      },
    );
    if (source == null || !mounted) return;
    await _pickImage(source);
  }

  Future<void> _pickImage(ImageSource source) async {
    try {
      final file = await _picker.pickImage(
        source: source,
        maxWidth: 1200,
        imageQuality: 85,
        preferredCameraDevice: CameraDevice.front,
      );
      if (file == null || !mounted) return;
      setState(() => _avatarFilePath = file.path);
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Не удалось получить фото. Проверьте доступ к камере.'),
          behavior: SnackBarBehavior.floating,
        ),
      );
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
    final bioLen = _bioController.text.length;

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
                    child: _buildAvatar(user?.avatarDisplayUrl),
                  ),
                ),
                TextButton(
                  onPressed: _pickAvatar,
                  child: Text(
                    _avatarFilePath != null ||
                            (user?.avatarUrl?.isNotEmpty ?? false)
                        ? 'Изменить фото'
                        : 'Добавить фото',
                  ),
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
            'Расскажите о себе',
            style: textTheme.titleMedium,
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _bioController,
            maxLines: 8,
            maxLength: _bioMaxLen,
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
              counterText: '$bioLen/$_bioMaxLen',
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
                const Icon(Icons.auto_awesome, color: AppColors.accent, size: 20),
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
        ],
      ),
    );
  }
}
