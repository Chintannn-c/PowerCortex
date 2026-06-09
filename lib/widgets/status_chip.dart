import 'package:flutter/material.dart';
import '../core/utils/responsive.dart';
import '../core/theme/app_colors.dart';

enum StatusType { healthy, warning, critical, offline, info }

class StatusChip extends StatelessWidget {
  final StatusType status;
  final String? label;

  const StatusChip({
    super.key,
    required this.status,
    this.label,
  });

  Color get _color {
    switch (status) {
      case StatusType.healthy:
        return AppColors.healthy;
      case StatusType.warning:
        return AppColors.warning;
      case StatusType.critical:
        return AppColors.critical;
      case StatusType.offline:
        return Colors.grey;
      case StatusType.info:
        return AppColors.info;
    }
  }

  String get _defaultLabel {
    switch (status) {
      case StatusType.healthy:
        return 'Healthy';
      case StatusType.warning:
        return 'Warning';
      case StatusType.critical:
        return 'Critical';
      case StatusType.offline:
        return 'Offline';
      case StatusType.info:
        return 'Info';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: _color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: _color.withOpacity(0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 7,
            height: 7,
            decoration: BoxDecoration(color: _color, shape: BoxShape.circle),
          ),
          context.sw(6),
          Text(
            label ?? _defaultLabel,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: _color,
            ),
          ),
        ],
      ),
    );
  }
}
