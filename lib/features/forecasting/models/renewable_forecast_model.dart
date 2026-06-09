class RenewableForecastModel {
  final String id;
  final DateTime timestamp;
  final double temperature;
  final double humidity;
  final double windSpeed;
  final double cloudCover;
  final double solarGeneration;
  final double windGeneration;
  final double renewableTotal;

  RenewableForecastModel({
    required this.id,
    required this.timestamp,
    required this.temperature,
    required this.humidity,
    required this.windSpeed,
    required this.cloudCover,
    required this.solarGeneration,
    required this.windGeneration,
    required this.renewableTotal,
  });

  factory RenewableForecastModel.fromJson(Map<String, dynamic> json) {
    return RenewableForecastModel(
      id: json['_id'] ?? json['id'] ?? '',
      timestamp: DateTime.parse(json['timestamp'] ?? DateTime.now().toIso8601String()),
      temperature: (json['temperature'] as num?)?.toDouble() ?? 0.0,
      humidity: (json['humidity'] as num?)?.toDouble() ?? 0.0,
      windSpeed: (json['wind_speed'] as num?)?.toDouble() ?? 0.0,
      cloudCover: (json['cloud_cover'] as num?)?.toDouble() ?? 0.0,
      solarGeneration: (json['solar_generation'] as num?)?.toDouble() ?? 0.0,
      windGeneration: (json['wind_generation'] as num?)?.toDouble() ?? 0.0,
      renewableTotal: (json['renewable_total'] as num?)?.toDouble() ?? 0.0,
    );
  }
}
