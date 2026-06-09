import 'package:flutter/material.dart';

import '../core/utils/responsive.dart';

class ChartContainer extends StatelessWidget {
  final String title;
  final String? subtitle;
  final Widget chart;
  final List<Widget>? actions;

  const ChartContainer({
    super.key,
    required this.title,
    this.subtitle,
    required this.chart,
    this.actions,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(title, style: theme.textTheme.labelLarge),
                      if (subtitle != null) ...[
                        context.sh(2),
                        Text(subtitle!, style: theme.textTheme.bodySmall),
                      ],
                    ],
                  ),
                ),
                if (actions != null) ...actions!,
              ],
            ),
            context.sh(16),
            SizedBox(height: 200, child: chart),
          ],
        ),
      ),
    );
  }
}
