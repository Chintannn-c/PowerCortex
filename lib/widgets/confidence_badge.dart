import 'package:flutter/material.dart';
import '../core/utils/responsive.dart';
import '../core/theme/app_colors.dart';

class ConfidenceBadge extends StatelessWidget {
  final double score;

  const ConfidenceBadge({super.key, required this.score});

  Color get _color {
    if (score >= 90.0) return AppColors.healthy;
    if (score >= 75.0) return AppColors.warning;
    return AppColors.critical;
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: _color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: _color.withOpacity(0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.verified, size: 12, color: _color),
          context.sw(4),
          Text(
            '${score.toStringAsFixed(1)}%',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.bold,
              color: _color,
            ),
          ),
        ],
      ),
    );
  }
}
