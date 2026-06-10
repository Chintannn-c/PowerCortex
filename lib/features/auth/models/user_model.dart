class UserModel {
  final String id;
  final String fullName;
  final String email;
  final String department;
  final bool isActive;
  final bool isVerified;
  final bool twoFactorEnabled;
  final bool pushNotifications;
  final bool emailAlerts;
  final String createdAt;
  final String updatedAt;

  UserModel({
    required this.id,
    required this.fullName,
    required this.email,
    required this.department,
    required this.isActive,
    required this.isVerified,
    required this.twoFactorEnabled,
    required this.pushNotifications,
    required this.emailAlerts,
    required this.createdAt,
    required this.updatedAt,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id'] ?? '',
      fullName: json['full_name'] ?? '',
      email: json['email'] ?? '',
      department: json['department'] ?? 'General',
      isActive: json['is_active'] ?? true,
      isVerified: json['is_verified'] ?? false,
      twoFactorEnabled: json['two_factor_enabled'] ?? false,
      pushNotifications: json['push_notifications'] ?? true,
      emailAlerts: json['email_alerts'] ?? false,
      createdAt: json['created_at'] ?? '',
      updatedAt: json['updated_at'] ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'full_name': fullName,
      'email': email,
      'department': department,
      'is_active': isActive,
      'is_verified': isVerified,
      'two_factor_enabled': twoFactorEnabled,
      'push_notifications': pushNotifications,
      'email_alerts': emailAlerts,
      'created_at': createdAt,
      'updated_at': updatedAt,
    };
  }
}
