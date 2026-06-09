class ReportModel {
  final String id;
  final String name;
  final String date;
  final String type;
  final String size;

  ReportModel({
    required this.id,
    required this.name,
    required this.date,
    required this.type,
    required this.size,
  });

  factory ReportModel.fromJson(Map<String, dynamic> json) {
    return ReportModel(
      id: json['id'] ?? '',
      name: json['name'] ?? '',
      date: json['date'] ?? '',
      type: json['type'] ?? '',
      size: json['size'] ?? '',
    );
  }
}

class ModelMetric {
  final String label;
  final String value;
  ModelMetric(this.label, this.value);
}

class ModelPerformanceData {
  final List<ModelMetric> loadForecasting;
  final List<ModelMetric> transformerHealth;
  final List<ModelMetric> theftDetection;
  final List<ModelMetric> faultDetection;

  ModelPerformanceData({
    required this.loadForecasting,
    required this.transformerHealth,
    required this.theftDetection,
    required this.faultDetection,
  });

  factory ModelPerformanceData.fromJson(Map<String, dynamic> json) {
    final lf = json['load_forecasting'] as Map<String, dynamic>? ?? {};
    final th = json['transformer_health'] as Map<String, dynamic>? ?? {};
    final td = json['theft_detection'] as Map<String, dynamic>? ?? {};
    final fd = json['fault_detection'] as Map<String, dynamic>? ?? {};

    return ModelPerformanceData(
      loadForecasting: [
        ModelMetric('Accuracy', lf['accuracy'] ?? '96.4%'),
        ModelMetric('MAE', lf['mae'] ?? '12.4'),
        ModelMetric('RMSE', lf['rmse'] ?? '15.8'),
        ModelMetric('MAPE', lf['mape'] ?? '2.1%'),
      ],
      transformerHealth: [
        ModelMetric('Accuracy', th['accuracy'] ?? '94.1%'),
        ModelMetric('Precision', th['precision'] ?? '92.5%'),
        ModelMetric('Recall', th['recall'] ?? '91.0%'),
        ModelMetric('F1 Score', th['f1_score'] ?? '91.7%'),
      ],
      theftDetection: [
        ModelMetric('Detection Acc.', td['detection_acc'] ?? '95.2%'),
        ModelMetric('Anomalies', td['anomalies'] ?? '12'),
      ],
      faultDetection: [
        ModelMetric('Classification', fd['classification'] ?? '97.8%'),
        ModelMetric('Confidence', fd['confidence'] ?? '94.5%'),
      ],
    );
  }
}

class DataSourceModel {
  final String title;
  final String records;
  final String range;
  final String quality;

  DataSourceModel({
    required this.title,
    required this.records,
    required this.range,
    required this.quality,
  });

  factory DataSourceModel.fromJson(String title, Map<String, dynamic> json) {
    return DataSourceModel(
      title: title,
      records: json['records'] ?? '',
      range: json['range'] ?? '',
      quality: json['quality'] ?? '',
    );
  }
}
