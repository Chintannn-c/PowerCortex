import 'dart:async' as getx;
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:get/get.dart' as getx;
import '../../features/auth/auth_controller.dart';
import '../config/app_config.dart';

class ApiClient {
  static String _customBaseUrl = '';

  static String get customBaseUrl => _customBaseUrl;

  static set customBaseUrl(String value) {
    _customBaseUrl = value;
    _instance.dio.options.baseUrl = baseUrl;
  }

  static String get baseUrl => _customBaseUrl.isNotEmpty ? _customBaseUrl : AppConfig.apiBaseUrl;
  
  late final Dio dio;
  final FlutterSecureStorage secureStorage = const FlutterSecureStorage();

  static final ApiClient _instance = ApiClient._internal();

  factory ApiClient() {
    return _instance;
  }

  bool _isRefreshing = false;
  Future<void>? _refreshLock;

  ApiClient._internal() {
    dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: AppConfig.apiTimeout,
      receiveTimeout: AppConfig.apiTimeout,
      headers: {
        'Content-Type': 'application/json',
      },
    ));

    dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        // Automatically inject the access token if available
        final accessToken = await secureStorage.read(key: 'access_token');
        if (accessToken != null) {
          options.headers['Authorization'] = 'Bearer $accessToken';
        }
        return handler.next(options);
      },
      onError: (DioException error, handler) async {
        // Handle 401 Unauthorized globally
        if (error.response?.statusCode == 401 && !error.requestOptions.path.contains('/api/v1/auth/refresh')) {
          
          if (_isRefreshing) {
            // Wait for the active refresh to complete
            try {
              await _refreshLock;
              // Active refresh succeeded, get the new token and retry
              final newAccessToken = await secureStorage.read(key: 'access_token');
              if (newAccessToken != null) {
                return _retryOriginalRequest(error.requestOptions, newAccessToken, handler);
              }
            } catch (e) {
              return handler.next(error);
            }
          } else {
            _isRefreshing = true;
            final getx.Completer<void> completer = getx.Completer<void>();
            _refreshLock = completer.future;

            try {
              final refreshToken = await secureStorage.read(key: 'refresh_token');
              if (refreshToken != null) {
                // Call refresh endpoint with a separate dio instance to avoid interceptor loop
                final refreshDio = Dio(BaseOptions(baseUrl: baseUrl));
                final response = await refreshDio.post('/api/v1/auth/refresh', data: {
                  'refresh_token': refreshToken,
                });

                if (response.statusCode == 200 && response.data['success'] == true) {
                  final newAccessToken = response.data['data']['access_token'];
                  await secureStorage.write(key: 'access_token', value: newAccessToken);
                  
                  // Support rotation if server sends a new refresh_token
                  final newRefreshToken = response.data['data']['refresh_token'];
                  if (newRefreshToken != null && newRefreshToken != refreshToken) {
                    await secureStorage.write(key: 'refresh_token', value: newRefreshToken);
                  }

                  completer.complete();
                  _isRefreshing = false;

                  return _retryOriginalRequest(error.requestOptions, newAccessToken, handler);
                } else {
                  throw Exception('Refresh failed');
                }
              } else {
                throw Exception('No refresh token');
              }
            } catch (e) {
              completer.completeError(e);
              _isRefreshing = false;
              _triggerLogout();
              return handler.next(error);
            }
          }
        }
        return handler.next(error);
      },
    ));
  }

  Future<void> _retryOriginalRequest(RequestOptions requestOptions, String newAccessToken, ErrorInterceptorHandler handler) async {
    try {
      final opts = Options(
        method: requestOptions.method,
        headers: requestOptions.headers,
      );
      opts.headers?['Authorization'] = 'Bearer $newAccessToken';
      
      final retryDio = Dio(BaseOptions(baseUrl: baseUrl));
      final response = await retryDio.request(
        requestOptions.path,
        options: opts,
        data: requestOptions.data,
        queryParameters: requestOptions.queryParameters,
      );
      return handler.resolve(response);
    } catch (e) {
      if (e is DioException) {
        return handler.next(e);
      }
      return handler.next(DioException(requestOptions: requestOptions, error: e));
    }
  }

  void _triggerLogout() async {
    await secureStorage.deleteAll();
    try {
      if (getx.Get.isRegistered<AuthController>()) {
        getx.Get.find<AuthController>().logoutLocally();
      } else {
        getx.Get.offAllNamed('/login');
      }
    } catch (e) {
      // Get context not ready
    }
  }
}
