import 'package:city_vibe/theme/app_colors.dart';
import 'package:flutter/material.dart';

/// Переиспользуемое поле ввода для auth-экранов.
///
/// Stateful не нужен здесь: видимость пароля и контроллеры живут в родителе
/// ([LoginScreen]), а этот виджет — «глупый» UI-кирпичик (presentational).
class AuthTextField extends StatelessWidget {
  const AuthTextField({
    super.key,
    required this.controller,
    required this.hintText,
    required this.prefixIcon,
    this.obscureText = false,
    this.suffix,
    this.keyboardType,
    this.onChanged,
    this.readOnly = false,
    this.onTap,
  });

  /// Контроллер хранит текст поля. Обычно создаётся в State экрана.
  final TextEditingController controller;

  final String hintText;
  final IconData prefixIcon;

  /// true → точки вместо символов (пароль).
  final bool obscureText;

  /// Правая иконка (например, «глаз»).
  final Widget? suffix;

  final TextInputType? keyboardType;

  /// Колбэк при каждом изменении текста (для enable/disable кнопки).
  final ValueChanged<String>? onChanged;

  /// Только выбор (дата / город), без клавиатуры.
  final bool readOnly;

  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      obscureText: obscureText,
      keyboardType: keyboardType,
      onChanged: onChanged,
      readOnly: readOnly,
      onTap: onTap,
      style: const TextStyle(color: AppColors.textPrimary, fontSize: 15),
      cursorColor: AppColors.accent,
      decoration: InputDecoration(
        hintText: hintText,
        hintStyle: const TextStyle(color: AppColors.textSecondary),
        filled: true,
        fillColor: AppColors.fieldFill,
        prefixIcon: Icon(prefixIcon, color: AppColors.textSecondary, size: 22),
        suffixIcon: suffix,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        // Граница в трёх состояниях: обычная / в фокусе / ошибка (пока без валидации).
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: AppColors.fieldBorder),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: AppColors.accent, width: 1.4),
        ),
      ),
    );
  }
}
