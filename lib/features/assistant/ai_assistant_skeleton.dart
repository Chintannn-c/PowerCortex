import 'package:flutter/material.dart';

import '../../core/utils/responsive.dart';
import '../../core/theme/skeleton_theme.dart';
import '../../widgets/skeleton/skeletons.dart';

/// Full-page skeleton for the AI Assistant screen loading state.
///
/// Mimics the ChatGPT-style chat layout with message bubbles,
/// suggested prompts, and input bar.
class AIAssistantSkeleton extends StatelessWidget {
  const AIAssistantSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Column(
      children: [
        // Chat area
        const Expanded(
          child: Padding(
            padding: EdgeInsets.all(16),
            child: SkeletonAIMessage(),
          ),
        ),

        // Suggested prompts
        const SkeletonPromptChips(),
        context.sh(8),

        // Input bar
        Container(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
          decoration: BoxDecoration(
            color: SkeletonTheme.cardColor(context),
            border: Border(
              top: BorderSide(
                color: isDark
                    ? const Color(0xFF1E293B)
                    : const Color(0xFFE2E8F0),
              ),
            ),
          ),
          child: SkeletonShimmer(
            child: Row(
              children: [
                Expanded(
                  child: Container(
                    height: 46,
                    decoration: BoxDecoration(
                      color: SkeletonTheme.baseColor(context),
                      borderRadius: BorderRadius.circular(24),
                    ),
                  ),
                ),
                context.sw(10),
                const SkeletonCircle(size: 44),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
