import 'package:city_vibe/core/api/api_providers.dart';
import 'package:city_vibe/core/api/models/auth_models.dart';
import 'package:city_vibe/core/api/models/city.dart';
import 'package:city_vibe/core/network/api_exception.dart';
import 'package:city_vibe/core/router/app_router.dart';
import 'package:city_vibe/features/auth/presentation/otp_verify_screen.dart';
import 'package:city_vibe/features/auth/presentation/widgets/auth_text_field.dart';
import 'package:city_vibe/features/auth/presentation/widgets/gradient_button.dart';
import 'package:city_vibe/features/auth/presentation/widgets/login_background.dart';
import 'package:city_vibe/features/auth/presentation/widgets/scrolling_city_decor_bar.dart';
import 'package:city_vibe/features/auth/presentation/widgets/social_login_button.dart';
import 'package:city_vibe/theme/app_colors.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

/// Экран регистрации — вёрстка по макету + лёгкая UI-логика.
///
/// Фон и нижняя плашка города — те же, что на логине.
/// Города: SQLite-кэш (cache-first) + api-gateway `GET /cities`.
class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _passwordRepeatController = TextEditingController();
  final _birthdayController = TextEditingController();
  final _cityController = TextEditingController();

  bool _obscurePassword = true;
  bool _obscurePasswordRepeat = true;
  bool _acceptedTerms = false;
  DateTime? _birthday;

  List<City> _cities = const [];
  City? _selectedCity;
  bool _citiesLoading = true;
  String? _citiesError;
  bool _detectingCity = false;
  bool _submitting = false;

  /// 0..4 сегмента силы пароля (простая эвристика для UI).
  int get _passwordStrength {
    final p = _passwordController.text;
    if (p.isEmpty) return 0;
    var score = 0;
    if (p.length >= 8) score++;
    if (p.length >= 12) score++;
    if (RegExp(r'[A-ZА-Я]').hasMatch(p) && RegExp(r'[a-zа-я]').hasMatch(p)) {
      score++;
    }
    if (RegExp(r'[0-9]').hasMatch(p) ||
        RegExp(r'[^A-Za-zА-Яа-я0-9]').hasMatch(p)) {
      score++;
    }
    return score.clamp(0, 4);
  }

  bool get _canSubmit {
    return _nameController.text.trim().isNotEmpty &&
        _emailController.text.trim().isNotEmpty &&
        _passwordController.text.length >= 8 &&
        _passwordController.text == _passwordRepeatController.text &&
        _birthday != null &&
        _selectedCity != null &&
        _acceptedTerms;
  }

  @override
  void initState() {
    super.initState();
    // HTTP / GPS уходят в фоне, UI не блокируем.
    Future.microtask(() async {
      await Future.wait([
        _loadCities(),
        _detectCityFromGps(),
      ]);
    });
  }

  Future<void> _loadCities() async {
    setState(() {
      _citiesLoading = true;
      _citiesError = null;
    });
    try {
      final cities = await ref.read(citiesRepositoryProvider).getCities();
      if (!mounted) return;
      setState(() {
        _cities = cities;
        _citiesLoading = false;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _citiesLoading = false;
        _citiesError = e.message;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _citiesLoading = false;
        _citiesError = e.toString();
      });
    }
  }

  /// Запрос permission → GPS → nearest (API, иначе расчёт по кэшу).
  Future<void> _detectCityFromGps() async {
    if (kIsWeb) return;
    setState(() => _detectingCity = true);
    try {
      final serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Включите геолокацию, чтобы подставить город автоматически'),
            behavior: SnackBarBehavior.floating,
          ),
        );
        return;
      }

      var permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
      }
      if (permission == LocationPermission.denied) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Без доступа к геолокации выберите город вручную'),
            behavior: SnackBarBehavior.floating,
          ),
        );
        return;
      }
      if (permission == LocationPermission.deniedForever) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              'Геолокация запрещена в настройках. Выберите город вручную',
            ),
            behavior: SnackBarBehavior.floating,
          ),
        );
        return;
      }

      final pos = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.medium,
          timeLimit: Duration(seconds: 12),
        ),
      );

      final nearest = await ref.read(citiesRepositoryProvider).getNearestCity(
            lat: pos.latitude,
            lng: pos.longitude,
          );
      if (!mounted) return;
      // Не перетираем, если пользователь уже успел выбрать город вручную.
      if (_selectedCity != null) return;
      setState(() {
        _selectedCity = nearest;
        _cityController.text = nearest.name;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Не удалось определить город: ${e.message}'),
          behavior: SnackBarBehavior.floating,
        ),
      );
    } catch (_) {
      // Timeout / unavailable — молча оставляем ручной выбор.
    } finally {
      if (mounted) setState(() => _detectingCity = false);
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _passwordRepeatController.dispose();
    _birthdayController.dispose();
    _cityController.dispose();
    super.dispose();
  }

  void _onFieldsChanged([String? _]) => setState(() {});

  Future<void> _pickBirthday() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _birthday ?? DateTime(now.year - 18, now.month, now.day),
      firstDate: DateTime(1900),
      lastDate: now,
      builder: (context, child) {
        return Theme(
          data: Theme.of(context).copyWith(
            colorScheme: const ColorScheme.dark(
              primary: AppColors.accent,
              surface: AppColors.backgroundDeep,
            ),
          ),
          child: child!,
        );
      },
    );
    if (picked == null) return;
    setState(() {
      _birthday = picked;
      _birthdayController.text = DateFormat('dd.MM.yyyy').format(picked);
    });
  }

  Future<void> _pickCity() async {
    if (_citiesLoading) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Города ещё загружаются…'),
          behavior: SnackBarBehavior.floating,
        ),
      );
      return;
    }
    if (_cities.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(_citiesError ?? 'Список городов пуст'),
          behavior: SnackBarBehavior.floating,
          action: SnackBarAction(label: 'Повторить', onPressed: _loadCities),
        ),
      );
      return;
    }

    final selected = await showModalBottomSheet<City>(
      context: context,
      backgroundColor: AppColors.backgroundDeep,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return SafeArea(
          child: ListView(
            shrinkWrap: true,
            children: [
              const Padding(
                padding: EdgeInsets.fromLTRB(20, 16, 20, 8),
                child: Text(
                  'Выберите Ваш город',
                  style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 18,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              for (final city in _cities)
                ListTile(
                  title: Text(
                    city.name,
                    style: const TextStyle(color: AppColors.textPrimary),
                  ),
                  subtitle: city.region.isEmpty
                      ? null
                      : Text(
                          city.region,
                          style: const TextStyle(color: AppColors.textSecondary),
                        ),
                  onTap: () => Navigator.pop(context, city),
                ),
            ],
          ),
        );
      },
    );
    if (selected == null) return;
    setState(() {
      _selectedCity = selected;
      _cityController.text = selected.name;
    });
  }

  Future<void> _onRegisterPressed() async {
    if (!_canSubmit || _submitting) return;
    final city = _selectedCity;
    final birthday = _birthday;
    if (city == null || birthday == null) return;

    setState(() => _submitting = true);
    try {
      final challenge = await ref.read(authClientProvider).register(
            RegisterRequest(
              name: _nameController.text.trim(),
              identifier: _emailController.text.trim(),
              password: _passwordController.text,
              cityId: city.id,
              acceptTerms: _acceptedTerms,
              birthdate: DateFormat('yyyy-MM-dd').format(birthday),
            ),
          );
      if (!mounted) return;
      await context.push(
        AppRoutes.registerOtp,
        extra: OtpVerifyArgs(
          challenge: challenge,
          purpose: OtpPurpose.register,
        ),
      );
    } on ApiException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(e.message),
          behavior: SnackBarBehavior.floating,
        ),
      );
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return Scaffold(
      body: Stack(
        fit: StackFit.expand,
        children: [
          const LoginBackground(),
          SafeArea(
            child: Column(
              children: [
                Padding(
                  padding: const EdgeInsets.fromLTRB(8, 4, 8, 0),
                  child: Align(
                    alignment: Alignment.centerLeft,
                    child: IconButton(
                      onPressed: () => context.pop(),
                      tooltip: 'Назад',
                      icon: const Icon(Icons.chevron_left_rounded, size: 32),
                      color: AppColors.textPrimary,
                    ),
                  ),
                ),
                Expanded(
                  child: Center(
                    child: SingleChildScrollView(
                      padding: const EdgeInsets.fromLTRB(20, 0, 20, 180),
                      child: ConstrainedBox(
                        constraints: const BoxConstraints(maxWidth: 420),
                        child: Column(
                          children: [
                            // Место под эмблему на login_bg.png.
                            const SizedBox(height: 56),
                            Text('Регистрация', style: textTheme.headlineMedium),
                            const SizedBox(height: 8),
                            Text(
                              'Создайте аккаунт, чтобы сохранить любимые места и события',
                              textAlign: TextAlign.center,
                              style: textTheme.bodyMedium,
                            ),
                            const SizedBox(height: 20),
                            _RegisterCard(
                              textTheme: textTheme,
                              nameController: _nameController,
                              emailController: _emailController,
                              passwordController: _passwordController,
                              passwordRepeatController: _passwordRepeatController,
                              birthdayController: _birthdayController,
                              cityController: _cityController,
                              obscurePassword: _obscurePassword,
                              obscurePasswordRepeat: _obscurePasswordRepeat,
                              passwordStrength: _passwordStrength,
                              acceptedTerms: _acceptedTerms,
                              canSubmit: _canSubmit && !_submitting,
                              citiesLoading: _citiesLoading || _detectingCity,
                              submitLabel: _submitting
                                  ? 'Регистрируем…'
                                  : 'Зарегистрироваться',
                              onFieldsChanged: _onFieldsChanged,
                              onTogglePassword: () => setState(
                                () => _obscurePassword = !_obscurePassword,
                              ),
                              onTogglePasswordRepeat: () => setState(
                                () =>
                                    _obscurePasswordRepeat = !_obscurePasswordRepeat,
                              ),
                              onPickBirthday: _pickBirthday,
                              onPickCity: _pickCity,
                              onAcceptedChanged: (v) =>
                                  setState(() => _acceptedTerms = v ?? false),
                              onRegisterPressed:
                                  (_canSubmit && !_submitting)
                                      ? _onRegisterPressed
                                      : null,
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
          const Align(
            alignment: Alignment.bottomCenter,
            child: ScrollingCityDecorBar(),
          ),
        ],
      ),
    );
  }
}

class _RegisterCard extends StatelessWidget {
  const _RegisterCard({
    required this.textTheme,
    required this.nameController,
    required this.emailController,
    required this.passwordController,
    required this.passwordRepeatController,
    required this.birthdayController,
    required this.cityController,
    required this.obscurePassword,
    required this.obscurePasswordRepeat,
    required this.passwordStrength,
    required this.acceptedTerms,
    required this.canSubmit,
    required this.citiesLoading,
    required this.submitLabel,
    required this.onFieldsChanged,
    required this.onTogglePassword,
    required this.onTogglePasswordRepeat,
    required this.onPickBirthday,
    required this.onPickCity,
    required this.onAcceptedChanged,
    required this.onRegisterPressed,
  });

  final TextTheme textTheme;
  final TextEditingController nameController;
  final TextEditingController emailController;
  final TextEditingController passwordController;
  final TextEditingController passwordRepeatController;
  final TextEditingController birthdayController;
  final TextEditingController cityController;
  final bool obscurePassword;
  final bool obscurePasswordRepeat;
  final int passwordStrength;
  final bool acceptedTerms;
  final bool canSubmit;
  final bool citiesLoading;
  final String submitLabel;
  final ValueChanged<String> onFieldsChanged;
  final VoidCallback onTogglePassword;
  final VoidCallback onTogglePasswordRepeat;
  final VoidCallback onPickBirthday;
  final VoidCallback onPickCity;
  final ValueChanged<bool?> onAcceptedChanged;
  final VoidCallback? onRegisterPressed;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(20, 22, 20, 20),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: AppColors.cardBorder),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.35),
            blurRadius: 24,
            offset: const Offset(0, 12),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          AuthTextField(
            controller: nameController,
            hintText: 'Имя и фамилия',
            prefixIcon: Icons.person_outline_rounded,
            onChanged: onFieldsChanged,
          ),
          const SizedBox(height: 12),
          AuthTextField(
            controller: emailController,
            hintText: 'Email',
            prefixIcon: Icons.mail_outline_rounded,
            keyboardType: TextInputType.emailAddress,
            onChanged: onFieldsChanged,
          ),
          const SizedBox(height: 12),
          AuthTextField(
            controller: passwordController,
            hintText: 'Пароль',
            prefixIcon: Icons.lock_outline_rounded,
            obscureText: obscurePassword,
            onChanged: onFieldsChanged,
            suffix: IconButton(
              onPressed: onTogglePassword,
              tooltip: obscurePassword ? 'Показать пароль' : 'Скрыть пароль',
              icon: Icon(
                obscurePassword
                    ? Icons.visibility_outlined
                    : Icons.visibility_off_outlined,
                color: AppColors.textSecondary,
              ),
            ),
          ),
          const SizedBox(height: 8),
          _PasswordStrengthRow(strength: passwordStrength),
          const SizedBox(height: 12),
          AuthTextField(
            controller: passwordRepeatController,
            hintText: 'Повторите пароль',
            prefixIcon: Icons.lock_outline_rounded,
            obscureText: obscurePasswordRepeat,
            onChanged: onFieldsChanged,
            suffix: IconButton(
              onPressed: onTogglePasswordRepeat,
              tooltip:
                  obscurePasswordRepeat ? 'Показать пароль' : 'Скрыть пароль',
              icon: Icon(
                obscurePasswordRepeat
                    ? Icons.visibility_outlined
                    : Icons.visibility_off_outlined,
                color: AppColors.textSecondary,
              ),
            ),
          ),
          const SizedBox(height: 12),
          AuthTextField(
            controller: birthdayController,
            hintText: 'Дата рождения',
            prefixIcon: Icons.calendar_today_outlined,
            readOnly: true,
            onTap: onPickBirthday,
            onChanged: onFieldsChanged,
          ),
          const SizedBox(height: 12),
          AuthTextField(
            controller: cityController,
            hintText: citiesLoading ? 'Определяем город…' : 'Ваш город',
            prefixIcon: Icons.location_on_outlined,
            readOnly: true,
            onTap: onPickCity,
            onChanged: onFieldsChanged,
            suffix: citiesLoading
                ? const Padding(
                    padding: EdgeInsets.all(12),
                    child: SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    ),
                  )
                : const Icon(
                    Icons.keyboard_arrow_down_rounded,
                    color: AppColors.textSecondary,
                  ),
          ),
          const SizedBox(height: 14),
          _TermsCheckbox(
            value: acceptedTerms,
            onChanged: onAcceptedChanged,
          ),
          const SizedBox(height: 16),
          GradientButton(
            label: submitLabel,
            onPressed: canSubmit ? onRegisterPressed : null,
          ),
          const SizedBox(height: 18),
          const _OrDivider(label: 'или зарегистрируйтесь с помощью'),
          const SizedBox(height: 14),
          const _SocialCircleRow(),
          const SizedBox(height: 18),
          Text.rich(
            TextSpan(
              style: textTheme.bodyMedium,
              children: [
                const TextSpan(text: 'Уже есть аккаунт? '),
                WidgetSpan(
                  alignment: PlaceholderAlignment.baseline,
                  baseline: TextBaseline.alphabetic,
                  child: GestureDetector(
                    onTap: () {
                      if (context.canPop()) {
                        context.pop();
                      } else {
                        context.go(AppRoutes.login);
                      }
                    },
                    child: Text(
                      'Войти',
                      style: textTheme.bodyMedium?.copyWith(
                        color: AppColors.accent,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ),
              ],
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}

class _PasswordStrengthRow extends StatelessWidget {
  const _PasswordStrengthRow({required this.strength});

  final int strength;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: Text(
            'Минимум 8 символов',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontSize: 12),
          ),
        ),
        Row(
          children: List.generate(4, (i) {
            final filled = i < strength;
            return Container(
              width: 22,
              height: 4,
              margin: EdgeInsets.only(left: i == 0 ? 0 : 4),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(2),
                color: filled
                    ? AppColors.accent
                    : AppColors.textSecondary.withValues(alpha: 0.35),
              ),
            );
          }),
        ),
      ],
    );
  }
}

class _TermsCheckbox extends StatelessWidget {
  const _TermsCheckbox({
    required this.value,
    required this.onChanged,
  });

  final bool value;
  final ValueChanged<bool?> onChanged;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 24,
          height: 24,
          child: Checkbox(
            value: value,
            onChanged: onChanged,
            side: const BorderSide(color: AppColors.fieldBorder),
            activeColor: AppColors.accent,
            materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Text.rich(
            TextSpan(
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontSize: 12),
              children: [
                const TextSpan(text: 'Я принимаю условия '),
                WidgetSpan(
                  alignment: PlaceholderAlignment.baseline,
                  baseline: TextBaseline.alphabetic,
                  child: GestureDetector(
                    onTap: () {},
                    child: const Text(
                      'Пользовательского соглашения',
                      style: TextStyle(
                        color: AppColors.accent,
                        fontWeight: FontWeight.w600,
                        fontSize: 12,
                      ),
                    ),
                  ),
                ),
                const TextSpan(text: ' и '),
                WidgetSpan(
                  alignment: PlaceholderAlignment.baseline,
                  baseline: TextBaseline.alphabetic,
                  child: GestureDetector(
                    onTap: () {},
                    child: const Text(
                      'Политики конфиденциальности',
                      style: TextStyle(
                        color: AppColors.accent,
                        fontWeight: FontWeight.w600,
                        fontSize: 12,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _SocialCircleRow extends StatelessWidget {
  const _SocialCircleRow();

  bool get _isAppleOs =>
      defaultTargetPlatform == TargetPlatform.iOS ||
      defaultTargetPlatform == TargetPlatform.macOS;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        _SocialCircle(
          background: AppColors.googleButton,
          child: const GoogleMark(),
          onTap: () {},
        ),
        if (_isAppleOs) ...[
          const SizedBox(width: 14),
          _SocialCircle(
            background: AppColors.appleButton,
            child: const Icon(Icons.apple, color: Colors.white, size: 22),
            onTap: () {},
          ),
        ],
        const SizedBox(width: 14),
        _SocialCircle(
          background: const Color(0xFF0077FF),
          child: const Text(
            'VK',
            style: TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.w800,
              fontSize: 13,
            ),
          ),
          onTap: () {},
        ),
        const SizedBox(width: 14),
        _SocialCircle(
          background: const Color(0xFF2AABEE),
          child: const Icon(Icons.send_rounded, color: Colors.white, size: 18),
          onTap: () {},
        ),
      ],
    );
  }
}

class _SocialCircle extends StatelessWidget {
  const _SocialCircle({
    required this.background,
    required this.child,
    required this.onTap,
  });

  final Color background;
  final Widget child;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: background,
      shape: const CircleBorder(),
      child: InkWell(
        customBorder: const CircleBorder(),
        onTap: onTap,
        child: SizedBox(
          width: 48,
          height: 48,
          child: Center(child: child),
        ),
      ),
    );
  }
}

class _OrDivider extends StatelessWidget {
  const _OrDivider({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    final line = Expanded(
      child: Container(height: 1, color: const Color(0x33FFFFFF)),
    );
    return Row(
      children: [
        line,
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 10),
          child: Text(
            label,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontSize: 12),
          ),
        ),
        line,
      ],
    );
  }
}
