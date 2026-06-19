import 'package:flutter/material.dart';

import '../../core/utils/responsive.dart';
import 'skeleton_container.dart';
import '../../core/theme/skeleton_theme.dart';

/// Skeleton placeholder for the AI Assistant chat interface.
///
/// Shows a welcome message bubble, user bubble, assistant response bubble,
/// and a typing indicator to simulate the full conversation loading state.
class SkeletonAIMessage extends StatelessWidget {
  const SkeletonAIMessage({super.key});

  @override
  Widget build(BuildContext context) {
    return SkeletonShimmer(
      child: SingleChildScrollView(
        physics: const NeverScrollableScrollPhysics(),
        child: Column(
          children: [
            // Assistant welcome message
            _botBubble(context, 180),
            context.sh(16),
            // User message
            _userBubble(context, 140),
            context.sh(16),
            // Assistant response
            _botBubble(context, 220),
            context.sh(16),
            // Typing indicator
            _typingIndicator(context),
          ],
        ),
      ),
    );
  }

  Widget _botBubble(BuildContext context, double height) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SkeletonCircle(size: 34),
          context.sw(8),
          Container(
            width: MediaQuery.of(context).size.width * 0.6,
            constraints: const BoxConstraints(maxWidth: 400),
            height: height,
            decoration: BoxDecoration(
              color: SkeletonTheme.baseColor(context),
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(16),
                topRight: Radius.circular(16),
                bottomRight: Radius.circular(16),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _userBubble(BuildContext context, double height) {
    return Align(
      alignment: Alignment.centerRight,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.end,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: MediaQuery.of(context).size.width * 0.5,
            constraints: const BoxConstraints(maxWidth: 320),
            height: height,
            decoration: BoxDecoration(
              color: SkeletonTheme.baseColor(context),
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(16),
                topRight: Radius.circular(16),
                bottomLeft: Radius.circular(16),
              ),
            ),
          ),
          context.sw(8),
          const SkeletonCircle(size: 34),
        ],
      ),
    );
  }

  Widget _typingIndicator(BuildContext context) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Row(
        children: [
          const SkeletonCircle(size: 34),
          context.sw(8),
          Container(
            width: 72,
            height: 36,
            decoration: BoxDecoration(
              color: SkeletonTheme.baseColor(context),
              borderRadius: BorderRadius.circular(18),
            ),
          ),
        ],
      ),
    );
  }
}

/// Skeleton for the suggested prompt chips row.
class SkeletonPromptChips extends StatelessWidget {
  const SkeletonPromptChips({super.key});

  @override
  Widget build(BuildContext context) {
    return SkeletonShimmer(
      child: SizedBox(
        height: 38,
        child: ListView.separated(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.symmetric(horizontal: 16),
          itemCount: 4,
          separatorBuilder: (_, __) => context.sw(8),
          itemBuilder: (_, __) => Container(
            width: 150,
            decoration: BoxDecoration(
              color: SkeletonTheme.baseColor(context),
              borderRadius: BorderRadius.circular(20),
            ),
          ),
        ),
      ),
    );
  }
}
