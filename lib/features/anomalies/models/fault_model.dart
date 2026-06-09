import '../../../widgets/status_chip.dart';

class FaultModel {
  final String id;
  final String faultId;
  final String faultType;
  final String assetName;
  final StatusType severity;
  final double probability;
  final String status; // Active or Resolved
  final double voltage;
  final double current;
  final double frequency;
  final DateTime detectedAt;

  FaultModel({
    required this.id,
    required this.faultId,
    required this.faultType,
    required this.assetName,
    required this.severity,
    required this.probability,
    required this.status,
    required this.voltage,
    required this.current,
    required this.frequency,
    required this.detectedAt,
  });

  factory FaultModel.fromJson(Map<String, dynamic> json) {
    final severityStr = json['severity'] ?? 'Low';
    StatusType severityType;
    if (severityStr == 'Critical') {
      severityType = StatusType.critical;
    } else if (severityStr == 'High') {
      severityType = StatusType.warning;
    } else if (severityStr == 'Medium') {
      severityType = StatusType.healthy; // Maps to green
    } else {
      severityType = StatusType.info;    // Maps to blue
    }

    DateTime parsedDate;
    try {
      parsedDate = json['detected_at'] != null
          ? DateTime.parse(json['detected_at'])
          : DateTime.now();
    } catch (_) {
      parsedDate = DateTime.now();
    }

    return FaultModel(
      id: json['_id'] ?? json['id'] ?? '',
      faultId: json['fault_id'] ?? '',
      faultType: json['fault_type'] ?? '',
      assetName: json['asset_name'] ?? json['asset'] ?? '',
      severity: severityType,
      probability: (json['probability'] as num?)?.toDouble() ?? 0.0,
      status: json['status'] ?? 'Active',
      voltage: (json['voltage'] as num?)?.toDouble() ?? 0.0,
      current: (json['current'] as num?)?.toDouble() ?? 0.0,
      frequency: (json['frequency'] as num?)?.toDouble() ?? 0.0,
      detectedAt: parsedDate,
    );
  }
}

class FaultDashboardSummary {
  final int activeFaults;
  final int resolvedToday;
  final int critical;
  final int high;
  final int medium;
  final int low;

  FaultDashboardSummary({
    required this.activeFaults,
    required this.resolvedToday,
    required this.critical,
    required this.high,
    required this.medium,
    required this.low,
  });

  factory FaultDashboardSummary.fromJson(Map<String, dynamic> json) {
    return FaultDashboardSummary(
      activeFaults: json['active_faults'] as int? ?? 0,
      resolvedToday: json['resolved_today'] as int? ?? 0,
      critical: json['critical'] as int? ?? 0,
      high: json['high'] as int? ?? 0,
      medium: json['medium'] as int? ?? 0,
      low: json['low'] as int? ?? 0,
    );
  }
}

class FaultTimelinePoint {
  final String date;
  final int count;

  FaultTimelinePoint({required this.date, required this.count});

  factory FaultTimelinePoint.fromJson(Map<String, dynamic> json) {
    return FaultTimelinePoint(
      date: json['date'] ?? '',
      count: json['count'] as int? ?? 0,
    );
  }
}
