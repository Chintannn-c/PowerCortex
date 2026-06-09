class BackendServiceInfo {
  final String name;
  final String status;
  final String uptime;
  final int requestsPerMinute;
  final double cpuUsage;
  final double memoryUsage;
  final double latencyMs;

  BackendServiceInfo({
    required this.name,
    required this.status,
    required this.uptime,
    required this.requestsPerMinute,
    required this.cpuUsage,
    required this.memoryUsage,
    required this.latencyMs,
  });

  factory BackendServiceInfo.fromJson(Map<String, dynamic> json) {
    return BackendServiceInfo(
      name: json['name'] ?? '',
      status: json['status'] ?? '',
      uptime: json['uptime'] ?? '',
      requestsPerMinute: json['requests_per_minute'] ?? 0,
      cpuUsage: (json['cpu_usage'] as num?)?.toDouble() ?? 0.0,
      memoryUsage: (json['memory_usage'] as num?)?.toDouble() ?? 0.0,
      latencyMs: (json['latency_ms'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

class DatabaseServiceInfo {
  final String name;
  final String status;
  final double storageUsedGb;
  final double storageTotalGb;
  final int collections;
  final int readOpsPerSecond;
  final double latencyMs;

  DatabaseServiceInfo({
    required this.name,
    required this.status,
    required this.storageUsedGb,
    required this.storageTotalGb,
    required this.collections,
    required this.readOpsPerSecond,
    required this.latencyMs,
  });

  factory DatabaseServiceInfo.fromJson(Map<String, dynamic> json) {
    return DatabaseServiceInfo(
      name: json['name'] ?? '',
      status: json['status'] ?? '',
      storageUsedGb: (json['storage_used_gb'] as num?)?.toDouble() ?? 0.0,
      storageTotalGb: (json['storage_total_gb'] as num?)?.toDouble() ?? 0.0,
      collections: json['collections'] ?? 0,
      readOpsPerSecond: json['read_ops_per_second'] ?? 0,
      latencyMs: (json['latency_ms'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

class AIEngineInfo {
  final String name;
  final String status;
  final double latencyMs;
  final int tokensToday;

  AIEngineInfo({
    required this.name,
    required this.status,
    required this.latencyMs,
    required this.tokensToday,
  });

  factory AIEngineInfo.fromJson(Map<String, dynamic> json) {
    return AIEngineInfo(
      name: json['name'] ?? '',
      status: json['status'] ?? '',
      latencyMs: (json['latency_ms'] as num?)?.toDouble() ?? 0.0,
      tokensToday: json['tokens_today'] ?? 0,
    );
  }
}

class MLPipelineInfo {
  final double loadForecastingLatencyMs;
  final double transformerHealthLatencyMs;
  final double faultDetectionLatencyMs;
  final double theftDetectionLatencyMs;

  MLPipelineInfo({
    required this.loadForecastingLatencyMs,
    required this.transformerHealthLatencyMs,
    required this.faultDetectionLatencyMs,
    required this.theftDetectionLatencyMs,
  });

  factory MLPipelineInfo.fromJson(Map<String, dynamic> json) {
    return MLPipelineInfo(
      loadForecastingLatencyMs: (json['load_forecasting_latency_ms'] as num?)?.toDouble() ?? 0.0,
      transformerHealthLatencyMs: (json['transformer_health_latency_ms'] as num?)?.toDouble() ?? 0.0,
      faultDetectionLatencyMs: (json['fault_detection_latency_ms'] as num?)?.toDouble() ?? 0.0,
      theftDetectionLatencyMs: (json['theft_detection_latency_ms'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

class SystemHealthModel {
  final String overallStatus;
  final double overallHealthScore;
  final double failureProbability;
  final BackendServiceInfo backend;
  final DatabaseServiceInfo database;
  final AIEngineInfo aiEngine;
  final MLPipelineInfo mlPipeline;

  SystemHealthModel({
    required this.overallStatus,
    required this.overallHealthScore,
    required this.failureProbability,
    required this.backend,
    required this.database,
    required this.aiEngine,
    required this.mlPipeline,
  });

  factory SystemHealthModel.fromJson(Map<String, dynamic> json) {
    final services = json['services'] ?? {};
    return SystemHealthModel(
      overallStatus: json['overall_status'] ?? 'Healthy',
      overallHealthScore: (json['overall_health_score'] as num?)?.toDouble() ?? 100.0,
      failureProbability: (json['failure_probability'] as num?)?.toDouble() ?? 0.0,
      backend: BackendServiceInfo.fromJson(services['backend'] ?? {}),
      database: DatabaseServiceInfo.fromJson(services['database'] ?? {}),
      aiEngine: AIEngineInfo.fromJson(services['ai_engine'] ?? {}),
      mlPipeline: MLPipelineInfo.fromJson(services['ml_pipeline'] ?? {}),
    );
  }
}
