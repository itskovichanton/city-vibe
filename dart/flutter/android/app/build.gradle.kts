import java.util.Properties

plugins {
    id("com.android.application")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

val localProperties =
    Properties().apply {
        rootProject.file("local.properties").inputStream().use { load(it) }
    }
val flutterSdk =
    checkNotNull(localProperties.getProperty("flutter.sdk")) {
        "flutter.sdk not set in local.properties"
    }
val flutterProjectRoot = rootProject.projectDir.parentFile!!
val pluginRegistrantFile =
    file("src/main/java/io/flutter/plugins/GeneratedPluginRegistrant.java")

// Файл генерируется Flutter и в .gitignore — без него APK собирается, но плагины падают в runtime.
tasks.register<Exec>("flutterPubGet") {
    group = "flutter"
    description = "Generate GeneratedPluginRegistrant.java and sync plugins"
    workingDir(flutterProjectRoot)
    commandLine("$flutterSdk/bin/flutter", "pub", "get")
    inputs.file(flutterProjectRoot.resolve("pubspec.yaml"))
    inputs.file(flutterProjectRoot.resolve("pubspec.lock"))
    outputs.file(pluginRegistrantFile)
}

tasks.named("preBuild").configure {
    dependsOn("flutterPubGet")
}

android {
    namespace = "com.cityvibe.city_vibe"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    defaultConfig {
        // TODO: Specify your own unique Application ID (https://developer.android.com/studio/build/application-id.html).
        applicationId = "com.cityvibe.city_vibe"
        // You can update the following values to match your application needs.
        // For more information, see: https://flutter.dev/to/review-gradle-config.
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    buildTypes {
        release {
            // TODO: Add your own signing config for the release build.
            // Signing with the debug keys for now, so `flutter run --release` works.
            signingConfig = signingConfigs.getByName("debug")
        }
    }
}

kotlin {
    compilerOptions {
        jvmTarget = org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17
    }
}

flutter {
    source = "../.."
}

// Registrant пишется в начале compileFlutterBuild — javac/kotlin должны идти после.
androidComponents {
    onVariants { variant ->
        val variantCap =
            variant.name.replaceFirstChar { if (it.isLowerCase()) it.titlecase() else it.toString() }
        val flutterCompileTask = "compileFlutterBuild$variantCap"
        listOf(
            "compile${variantCap}JavaWithJavac",
            "compile${variantCap}Kotlin",
        ).forEach { compileTaskName ->
            tasks.matching { it.name == compileTaskName }.configureEach {
                dependsOn(tasks.matching { it.name == flutterCompileTask })
            }
        }
    }
}
