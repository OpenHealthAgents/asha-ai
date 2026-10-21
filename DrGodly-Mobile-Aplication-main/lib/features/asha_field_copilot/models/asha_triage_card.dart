enum TriageTrafficLight {
  red,
  amber,
  green,
}

class AshaTriageCard {
  final TriageTrafficLight light;
  final String title;
  final String subtitle;
  final List<String> dangerFlags;
  final List<String> careGapsBadges;
  final String? audioEducationUrl;
  final String? audioTitle;
  final String? audioDuration;
  final String primaryActionText;
  final String? referralFacility;
  final bool requiresImmediateReferral;

  const AshaTriageCard({
    required this.light,
    required this.title,
    required this.subtitle,
    this.dangerFlags = const [],
    this.careGapsBadges = const [],
    this.audioEducationUrl,
    this.audioTitle,
    this.audioDuration,
    required this.primaryActionText,
    this.referralFacility,
    this.requiresImmediateReferral = false,
  });

  factory AshaTriageCard.red({
    required String title,
    required String subtitle,
    required List<String> dangerFlags,
    required String referralFacility,
  }) {
    return AshaTriageCard(
      light: TriageTrafficLight.red,
      title: title,
      subtitle: subtitle,
      dangerFlags: dangerFlags,
      primaryActionText: '🚨 1-Tap Escalate to PHC (108)',
      referralFacility: referralFacility,
      requiresImmediateReferral: true,
    );
  }

  factory AshaTriageCard.amber({
    required String title,
    required String subtitle,
    required List<String> careGapsBadges,
  }) {
    return AshaTriageCard(
      light: TriageTrafficLight.amber,
      title: title,
      subtitle: subtitle,
      careGapsBadges: careGapsBadges,
      primaryActionText: '📋 Add to Due List for Next VHSND',
    );
  }

  factory AshaTriageCard.green({
    required String title,
    required String subtitle,
    required String audioEducationUrl,
    required String audioTitle,
    String audioDuration = '60s',
  }) {
    return AshaTriageCard(
      light: TriageTrafficLight.green,
      title: title,
      subtitle: subtitle,
      audioEducationUrl: audioEducationUrl,
      audioTitle: audioTitle,
      audioDuration: audioDuration,
      primaryActionText: '🔊 Play Verified Health Audio to Family',
    );
  }
}
