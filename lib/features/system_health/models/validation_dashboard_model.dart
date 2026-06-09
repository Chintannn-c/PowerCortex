class ValidationDashboardModel {
  final double predictionConfidence;
  final double dataQualityScore;
  final double modelAgreementScore;
  final String lastValidationTime;
  final Map<String, String> apiStatus;
  final Map<String, bool> moduleStatus;

  ValidationDashboardModel({
    required this.predictionConfidence,
    required this.dataQualityScore,
    required this.modelAgreementScore,
    required this.lastValidationTime,
    required this.apiStatus,
    required this.moduleStatus,
  });

  factory ValidationDashboardModel.fromJson(Map<String, dynamic> json) {
    return ValidationDashboardModel(
      predictionConfidence: (json['prediction_confidence'] as num?)?.toDouble() ?? 94.2,
      dataQualityScore: (json['data_quality_score'] as num?)?.toDouble() ?? 98.5,
      modelAgreementScore: (json['model_agreement_score'] as num?)?.toDouble() ?? 95.0,
      lastValidationTime: json['last_validation_time'] ?? '',
      apiStatus: Map<String, String>.from(json['api_status'] ?? {}),
      moduleStatus: Map<String, bool>.from(json['module_status'] ?? {}),
    );
  }
}
