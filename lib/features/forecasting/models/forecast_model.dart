class ForecastInfo {
  final double predictedDemand;
  final String unit;
  final double confidence;

  ForecastInfo({
    required this.predictedDemand,
    required this.unit,
    required this.confidence,
  });

  factory ForecastInfo.fromJson(Map<String, dynamic> json) {
    return ForecastInfo(
      predictedDemand: (json['predicted_demand'] as num).toDouble(),
      unit: json['unit'] ?? 'MW',
      confidence: (json['confidence'] as num).toDouble(),
    );
  }
}

class ForecastDocument {
  final String id;
  final String forecastType;
  final double predictedDemand;
  final double confidence;
  final double temperature;
  final int humidity;
  final double windSpeed;
  final int cloudCover;
  final List<String> insights;
  final DateTime createdAt;

  ForecastDocument({
    required this.id,
    required this.forecastType,
    required this.predictedDemand,
    required this.confidence,
    required this.temperature,
    required this.humidity,
    required this.windSpeed,
    required this.cloudCover,
    required this.insights,
    required this.createdAt,
  });

  factory ForecastDocument.fromJson(Map<String, dynamic> json) {
    return ForecastDocument(
      id: json['id'] ?? json['_id'] ?? '',
      forecastType: json['forecast_type'] ?? '',
      predictedDemand: (json['predicted_demand'] as num).toDouble(),
      confidence: (json['confidence'] as num).toDouble(),
      temperature: (json['temperature'] as num).toDouble(),
      humidity: (json['humidity'] as num).toInt(),
      windSpeed: (json['wind_speed'] as num).toDouble(),
      cloudCover: (json['cloud_cover'] as num).toInt(),
      insights: List<String>.from(json['insights'] ?? []),
      createdAt: DateTime.parse(json['created_at']),
    );
  }
}

class ChartPoint {
  final DateTime timestamp;
  final double actual;
  final double predicted;

  ChartPoint({
    required this.timestamp,
    required this.actual,
    required this.predicted,
  });

  factory ChartPoint.fromJson(Map<String, dynamic> json) {
    return ChartPoint(
      timestamp: DateTime.parse(json['timestamp']),
      actual: (json['actual'] as num).toDouble(),
      predicted: (json['predicted'] as num).toDouble(),
    );
  }
}

class DashboardSummary {
  final double currentDemand;
  final double nextHour;
  final double nextHourConfidence;
  final double nextDay;
  final double nextDayConfidence;
  final double nextWeek;
  final double nextWeekConfidence;
  final String peakTime;
  final double renewableContribution;
  final double mae;
  final double rmse;
  final double mape;
  final List<String> insights;

  DashboardSummary({
    required this.currentDemand,
    required this.nextHour,
    required this.nextHourConfidence,
    required this.nextDay,
    required this.nextDayConfidence,
    required this.nextWeek,
    required this.nextWeekConfidence,
    required this.peakTime,
    required this.renewableContribution,
    required this.mae,
    required this.rmse,
    required this.mape,
    required this.insights,
  });

  factory DashboardSummary.fromJson(Map<String, dynamic> json) {
    return DashboardSummary(
      currentDemand: (json['current_demand'] as num).toDouble(),
      nextHour: (json['next_hour'] as num).toDouble(),
      nextHourConfidence: (json['next_hour_confidence'] as num).toDouble(),
      nextDay: (json['next_day'] as num).toDouble(),
      nextDayConfidence: (json['next_day_confidence'] as num).toDouble(),
      nextWeek: (json['next_week'] as num).toDouble(),
      nextWeekConfidence: (json['next_week_confidence'] as num).toDouble(),
      peakTime: json['peak_time'] ?? '18:00',
      renewableContribution: (json['renewable_contribution'] as num).toDouble(),
      mae: (json['mae'] as num?)?.toDouble() ?? 481.72,
      rmse: (json['rmse'] as num?)?.toDouble() ?? 650.83,
      mape: (json['mape'] as num?)?.toDouble() ?? 1.54,
      insights: List<String>.from(json['insights'] ?? []),
    );
  }
}
