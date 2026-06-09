import '../../../widgets/status_chip.dart';

class TheftAlertModel {
  final String consumerId;
  final String consumerName;
  final String sector;
  final String city;
  final double currentConsumption;
  final double avgConsumption;
  final double powerFactor;
  final double theftProbability;
  final String riskLevel;
  final double deviationPercentage;
  final bool isSuspicious;
  final String status;
  final DateTime createdAt;

  TheftAlertModel({
    required this.consumerId,
    required this.consumerName,
    required this.sector,
    required this.city,
    required this.currentConsumption,
    required this.avgConsumption,
    required this.powerFactor,
    required this.theftProbability,
    required this.riskLevel,
    required this.deviationPercentage,
    required this.isSuspicious,
    required this.status,
    required this.createdAt,
  });

  StatusType get severityStatus {
    switch (riskLevel) {
      case 'High Risk':
        return StatusType.critical;
      case 'Medium Risk':
        return StatusType.warning;
      case 'Low Risk':
        return StatusType.info;
      default:
        return StatusType.healthy;
    }
  }

  factory TheftAlertModel.fromJson(Map<String, dynamic> json) {
    DateTime parsedDate;
    try {
      parsedDate = json['created_at'] != null
          ? DateTime.parse(json['created_at'])
          : DateTime.now();
    } catch (_) {
      parsedDate = DateTime.now();
    }

    return TheftAlertModel(
      consumerId: json['consumer_id'] ?? '',
      consumerName: json['consumer_name'] ?? '',
      sector: json['sector'] ?? '',
      city: json['city'] ?? '',
      currentConsumption: (json['current_consumption'] as num?)?.toDouble() ?? 0.0,
      avgConsumption: (json['avg_consumption'] as num?)?.toDouble() ?? 0.0,
      powerFactor: (json['power_factor'] as num?)?.toDouble() ?? 0.0,
      theftProbability: (json['theft_probability'] as num?)?.toDouble() ?? 0.0,
      riskLevel: json['risk_level'] ?? 'Normal',
      deviationPercentage: (json['deviation_percentage'] as num?)?.toDouble() ?? 0.0,
      isSuspicious: json['is_suspicious'] as bool? ?? false,
      status: json['status'] ?? 'Active',
      createdAt: parsedDate,
    );
  }
}

class TheftDashboardModel {
  final int suspiciousCount;
  final int highRiskCount;
  final int resolvedCount;
  final double averageProbability;

  TheftDashboardModel({
    required this.suspiciousCount,
    required this.highRiskCount,
    required this.resolvedCount,
    required this.averageProbability,
  });

  factory TheftDashboardModel.fromJson(Map<String, dynamic> json) {
    return TheftDashboardModel(
      suspiciousCount: json['suspicious_count'] as int? ?? 0,
      highRiskCount: json['high_risk_count'] as int? ?? 0,
      resolvedCount: json['resolved_count'] as int? ?? 0,
      averageProbability: (json['average_probability'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

class TheftDistributionPoint {
  final String name;
  final int value;

  TheftDistributionPoint({required this.name, required this.value});

  factory TheftDistributionPoint.fromJson(Map<String, dynamic> json) {
    return TheftDistributionPoint(
      name: json['name'] ?? '',
      value: json['value'] as int? ?? 0,
    );
  }
}

class TheftTrendPoint {
  final String month;
  final double actual;
  final double expected;

  TheftTrendPoint({required this.month, required this.actual, required this.expected});

  factory TheftTrendPoint.fromJson(Map<String, dynamic> json) {
    return TheftTrendPoint(
      month: json['month'] ?? '',
      actual: (json['actual'] as num?)?.toDouble() ?? 0.0,
      expected: (json['expected'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

class ConsumerInvestigationModel {
  final String consumerId;
  final String consumerName;
  final String sector;
  final String city;
  final double currentConsumption;
  final double avgConsumption;
  final double powerFactor;
  final List<double> monthlyUsage;
  final double theftProbability;
  final String riskLevel;
  final double deviationPercentage;
  final bool isSuspicious;
  final String aiExplanation;
  final String investigationNotes;

  ConsumerInvestigationModel({
    required this.consumerId,
    required this.consumerName,
    required this.sector,
    required this.city,
    required this.currentConsumption,
    required this.avgConsumption,
    required this.powerFactor,
    required this.monthlyUsage,
    required this.theftProbability,
    required this.riskLevel,
    required this.deviationPercentage,
    required this.isSuspicious,
    required this.aiExplanation,
    required this.investigationNotes,
  });

  factory ConsumerInvestigationModel.fromJson(Map<String, dynamic> json) {
    return ConsumerInvestigationModel(
      consumerId: json['consumer_id'] ?? '',
      consumerName: json['consumer_name'] ?? '',
      sector: json['sector'] ?? '',
      city: json['city'] ?? '',
      currentConsumption: (json['current_consumption'] as num?)?.toDouble() ?? 0.0,
      avgConsumption: (json['avg_consumption'] as num?)?.toDouble() ?? 0.0,
      powerFactor: (json['power_factor'] as num?)?.toDouble() ?? 0.0,
      monthlyUsage: List<double>.from((json['monthly_usage'] as List? ?? []).map((x) => (x as num).toDouble())),
      theftProbability: (json['theft_probability'] as num?)?.toDouble() ?? 0.0,
      riskLevel: json['risk_level'] ?? 'Normal',
      deviationPercentage: (json['deviation_percentage'] as num?)?.toDouble() ?? 0.0,
      isSuspicious: json['is_suspicious'] as bool? ?? false,
      aiExplanation: json['ai_explanation'] ?? '',
      investigationNotes: json['investigation_notes'] ?? '',
    );
  }
}
