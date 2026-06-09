import 'package:dio/dio.dart';
import 'package:guvnl_project/core/api/api_client.dart';

class AuthRepository {
  final ApiClient _apiClient = ApiClient();

  Future<Map<String, dynamic>> login(String email, String password) async {
    try {
      final response = await _apiClient.dio.post('/api/v1/auth/login', data: {
        'email': email,
        'password': password,
      });
      return response.data;
    } on DioException catch (e) {
      if (e.response != null && e.response?.data is Map) {
        return e.response?.data;
      }
      return {'success': false, 'message': 'Network error occurred'};
    }
  }

  Future<Map<String, dynamic>> register(String fullName, String email, String password, String department) async {
    try {
      final response = await _apiClient.dio.post('/api/v1/auth/register', data: {
        'full_name': fullName,
        'email': email,
        'password': password,
        'department': department,
      });
      return response.data;
    } on DioException catch (e) {
      if (e.response != null && e.response?.data is Map) {
        return e.response?.data;
      }
      return {'success': false, 'message': 'Network error occurred'};
    }
  }

  Future<Map<String, dynamic>> logout(String refreshToken) async {
    try {
      final response = await _apiClient.dio.post('/api/v1/auth/logout', data: {
        'refresh_token': refreshToken,
      });
      return response.data;
    } on DioException catch (e) {
      if (e.response != null && e.response?.data is Map) {
        return e.response?.data;
      }
      return {'success': false, 'message': 'Network error occurred'};
    }
  }

  Future<Map<String, dynamic>> getCurrentUser() async {
    try {
      final response = await _apiClient.dio.get('/api/v1/auth/me');
      return response.data;
    } on DioException catch (e) {
      if (e.response != null && e.response?.data is Map) {
        return e.response?.data;
      }
      return {'success': false, 'message': 'Network error occurred'};
    }
  }

  Future<Map<String, dynamic>> updateUser(String userId, Map<String, dynamic> data) async {
    try {
      final response = await _apiClient.dio.put('/api/v1/users/$userId', data: data);
      return response.data;
    } on DioException catch (e) {
      if (e.response != null && e.response?.data is Map) {
        return e.response?.data;
      }
      return {'success': false, 'message': 'Network error occurred'};
    }
  }

  Future<Map<String, dynamic>> changePassword(String currentPassword, String newPassword) async {
    try {
      final response = await _apiClient.dio.post('/api/v1/auth/change-password', data: {
        'current_password': currentPassword,
        'new_password': newPassword,
      });
      return response.data;
    } on DioException catch (e) {
      if (e.response != null && e.response?.data is Map) {
        return e.response?.data;
      }
      return {'success': false, 'message': 'Network error occurred'};
    }
  }

  Future<Map<String, dynamic>> setup2FA() async {
    try {
      final response = await _apiClient.dio.get('/api/v1/auth/2fa/setup');
      return response.data;
    } on DioException catch (e) {
      if (e.response != null && e.response?.data is Map) {
        return e.response?.data;
      }
      return {'success': false, 'message': 'Network error occurred'};
    }
  }

  Future<Map<String, dynamic>> verify2FA(String code) async {
    try {
      final response = await _apiClient.dio.post('/api/v1/auth/2fa/verify', data: {
        'code': code,
      });
      return response.data;
    } on DioException catch (e) {
      if (e.response != null && e.response?.data is Map) {
        return e.response?.data;
      }
      return {'success': false, 'message': 'Network error occurred'};
    }
  }

  Future<Map<String, dynamic>> loginWith2FA(String tempToken, String code) async {
    try {
      final response = await _apiClient.dio.post('/api/v1/auth/login/2fa', data: {
        'temp_token': tempToken,
        'code': code,
      });
      return response.data;
    } on DioException catch (e) {
      if (e.response != null && e.response?.data is Map) {
        return e.response?.data;
      }
      return {'success': false, 'message': 'Network error occurred'};
    }
  }

  Future<Map<String, dynamic>> get2FACode() async {
    try {
      final response = await _apiClient.dio.get('/api/v1/auth/2fa/code');
      return response.data;
    } on DioException catch (e) {
      if (e.response != null && e.response?.data is Map) {
        return e.response?.data;
      }
      return {'success': false, 'message': 'Network error occurred'};
    }
  }

  Future<Map<String, dynamic>> disable2FA() async {
    try {
      final response = await _apiClient.dio.post('/api/v1/auth/2fa/disable');
      return response.data;
    } on DioException catch (e) {
      if (e.response != null && e.response?.data is Map) {
        return e.response?.data;
      }
      return {'success': false, 'message': 'Network error occurred'};
    }
  }

  Future<Map<String, dynamic>> get2FACodeForLogin(String tempToken) async {
    try {
      final response = await _apiClient.dio.post('/api/v1/auth/login/2fa/code', data: {
        'temp_token': tempToken,
      });
      return response.data;
    } on DioException catch (e) {
      if (e.response != null && e.response?.data is Map) {
        return e.response?.data;
      }
      return {'success': false, 'message': 'Network error occurred'};
    }
  }
}
