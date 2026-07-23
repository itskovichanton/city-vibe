import 'package:flutter/material.dart';

/// Цвета приложения CityVibe — вынесены в одно место.
///
/// Зачем отдельный файл?
/// 1) Дизайн-токены (как CSS variables): меняешь здесь — меняется везде.
/// 2) Легче держать экран «в стиле макета», не разбрасывая `#7B2CFF` по виджетам.
///
/// Значения подобраны по присланному макету логина (neon night / purple).
abstract final class AppColors {
  /// Почти чёрный фон «ночи города».
  static const background = Color(0xFF07060C);

  /// Глубокий индиго под карточкой.
  static const backgroundDeep = Color(0xFF120B1F);

  /// Полупрозрачная «стеклянная» карточка формы.
  static const card = Color(0xCC1A1228); // ~80% opacity

  /// Обводка карточки / полей.
  static const cardBorder = Color(0x33FFFFFF);

  /// Основной акцент (ссылки, фокус).
  static const accent = Color(0xFFB24BFF);

  /// Начало градиента кнопки «Войти».
  static const gradientStart = Color(0xFF9B3CFF);

  /// Конец градиента кнопки «Войти».
  static const gradientEnd = Color(0xFF5B2BFF);

  /// Основной текст.
  static const textPrimary = Color(0xFFFFFFFF);

  /// Вторичный текст (подзаголовки, плейсхолдеры).
  static const textSecondary = Color(0xFFB7B0C5);

  /// Фон текстовых полей.
  static const fieldFill = Color(0xFF15101F);

  /// Обводка поля.
  static const fieldBorder = Color(0x44FFFFFF);

  /// Кнопка Google — белая.
  static const googleButton = Color(0xFFFFFFFF);

  /// Кнопка Apple — чёрная.
  static const appleButton = Color(0xFF000000);

  /// Disabled-состояние primary-кнопки (приглушённый градиент).
  static const disabledButton = Color(0xFF3A2A55);
}
