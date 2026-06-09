import '../../../widgets/status_chip.dart';

class TransformerModel {
  final String id;
  final String assetId;
  final String name;
  final String type;
  final double temperature;
  final double voltage;
  final double current;
  final double oilLevel;
  final double loadPercentage;
  final double healthScore;
  final double riskScore;
  final double failureProbability;
  final StatusType status;
  final DateTime lastUpdated;

  TransformerModel({
    required this.id,
    required this.assetId,
    required this.name,
    required this.type,
    required this.temperature,
    required this.voltage,
    required this.current,
    required this.oilLevel,
    required this.loadPercentage,
    required this.healthScore,
    required this.riskScore,
    required this.failureProbability,
    required this.status,
    required this.lastUpdated,
  });

  factory TransformerModel.fromJson(Map<String, dynamic> json) {
    final statusStr = json['status'] ?? 'Healthy';
    StatusType statusType;
    if (statusStr == 'Healthy') {
      statusType = StatusType.healthy;
    } else if (statusStr == 'Warning') {
      statusType = StatusType.warning;
    } else if (statusStr == 'Critical') {
      statusType = StatusType.critical;
    } else {
      statusType = StatusType.offline;
    }

    DateTime parsedDate;
    try {
      parsedDate = json['last_updated'] != null
          ? DateTime.parse(json['last_updated'])
          : DateTime.now();
    } catch (_) {
      parsedDate = DateTime.now();
    }

    return TransformerModel(
      id: json['_id'] ?? json['id'] ?? '',
      assetId: json['asset_id'] ?? '',
      name: json['name'] ?? '',
      type: json['type'] ?? '',
      temperature: (json['temperature'] as num?)?.toDouble() ?? 0.0,
      voltage: (json['voltage'] as num?)?.toDouble() ?? 0.0,
      current: (json['current'] as num?)?.toDouble() ?? 0.0,
      oilLevel: (json['oil_level'] as num?)?.toDouble() ?? 0.0,
      loadPercentage: (json['load_percentage'] as num?)?.toDouble() ?? 0.0,
      healthScore: (json['health_score'] as num?)?.toDouble() ?? 0.0,
      riskScore: (json['risk_score'] as num?)?.toDouble() ?? 0.0,
      failureProbability: (json['failure_probability'] as num?)?.toDouble() ?? 0.0,
      status: statusType,
      lastUpdated: parsedDate,
    );
  }
}

class TransformerDashboardSummary {
  final int total;
  final int healthy;
  final int warning;
  final int critical;

  TransformerDashboardSummary({
    required this.total,
    required this.healthy,
    required this.warning,
    required this.critical,
  });

  factory TransformerDashboardSummary.fromJson(Map<String, dynamic> json) {
    return TransformerDashboardSummary(
      total: json['total'] as int? ?? json['total_assets'] as int? ?? 0,
      healthy: json['healthy'] as int? ?? 0,
      warning: json['warning'] as int? ?? 0,
      critical: json['critical'] as int? ?? 0,
    );
  }
}
