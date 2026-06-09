class UserModel {
  final String id;
  final String fullName;
  final String email;
  final String department;
  final bool isActive;
  final bool isVerified;
  final bool twoFactorEnabled;
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
      'created_at': createdAt,
      'updated_at': updatedAt,
    };
  }
}
