import 'dart:convert';
import 'package:dio/dio.dart';
import '../models/asha_triage_card.dart';
import '../models/asha_care_gap.dart';

/// Service bridging the Flutter client to the langcare-mcp-fhir-main MCP Server
class AshaMcpBridgeService {
  final Dio _dio;
  final String mcpServerUrl;

  AshaMcpBridgeService({
    Dio? dio,
    this.mcpServerUrl = 'http://10.0.2.2:8080',
  }) : _dio = dio ??
            Dio(BaseOptions(
              connectTimeout: const Duration(seconds: 10),
              receiveTimeout: const Duration(seconds: 10),
            ));

  /// Evaluates clinical parameters and generates Traffic-Light Triage Cards
  Future<List<AshaTriageCard>> generateTriageCards({
    required String patientId,
    required String transcript,
    required Map<String, dynamic> vitals,
    required List<AshaCareGap> activeCareGaps,
    bool isMaternal = true,
    bool isPediatric = false,
    String languageCode = 'hi',
  }) async {
    List<AshaTriageCard> cards = [];

    final systolic = (vitals['systolic_bp'] as num?)?.toDouble();
    final diastolic = (vitals['diastolic_bp'] as num?)?.toDouble();
    final hb = (vitals['hemoglobin'] as num?)?.toDouble();
    final spo2 = (vitals['spo2'] as num?)?.toDouble();
    final temp = (vitals['temperature_c'] as num?)?.toDouble();

    // 1. Evaluate Red Flags (High-Risk Emergency Rules)
    List<String> dangerFlags = [];

    if (isMaternal) {
      if ((systolic != null && systolic >= 140) || (diastolic != null && diastolic >= 90)) {
        dangerFlags.add('Pre-eclampsia Risk: BP ${systolic?.toInt()}/${diastolic?.toInt()} mmHg (>= 140/90)');
      }
      if (hb != null && hb < 7.0) {
        dangerFlags.add('Severe Maternal Anemia: Hb $hb g/dL (< 7.0 g/dL)');
      }
      if (transcript.contains('bleeding') || transcript.contains('khoon')) {
        dangerFlags.add('Vaginal Bleeding: Antepartum Hemorrhage Danger');
      }
      if (transcript.contains('sujan') || transcript.contains('edema')) {
        dangerFlags.add('Pedal Edema / Facial Swelling');
      }
    }

    if (isPediatric) {
      if (transcript.contains('chest indrawing') || transcript.contains('pasli')) {
        dangerFlags.add('Severe Pneumonia: Lower chest indrawing observed');
      }
      if (transcript.contains('breastfeed') || transcript.contains('doodh')) {
        dangerFlags.add('Inability to breastfeed / feed');
      }
      if (transcript.contains('convulsion') || transcript.contains('daura')) {
        dangerFlags.add('Neurological Danger Sign: Convulsions/fits');
      }
      if (spo2 != null && spo2 < 92) {
        dangerFlags.add('Severe Hypoxemia: SpO2 $spo2% (< 92%)');
      }
    }

    // RED CARD: If any danger flags are triggered
    if (dangerFlags.isNotEmpty) {
      cards.add(AshaTriageCard.red(
        title: isMaternal ? 'High-Risk Pregnancy Alert' : 'Severe Pediatric Infection Alert',
        subtitle: '${dangerFlags.length} immediate danger signs detected during visit.',
        dangerFlags: dangerFlags,
        referralFacility: 'First Referral Unit (FRU) / District Hospital via 108 Ambulance',
      ));
    }

    // AMBER CARD: If care gaps exist for this household
    if (activeCareGaps.isNotEmpty) {
      final badges = activeCareGaps.map((g) => '${g.title} (${g.daysOverdue}d overdue)').toList();
      cards.add(AshaTriageCard.amber(
        title: 'Household Care Gaps Identified',
        subtitle: '${activeCareGaps.length} preventive health interventions are due for family members.',
        careGapsBadges: badges,
      ));
    }

    // GREEN CARD: Routine education audio clip from bezs-filenest
    final lang = languageCode.substring(0, 2).toLowerCase();
    String clipTitle = 'गर्भावस्था में स्वास्थ्य व खतरे के संकेत (60s)';
    String streamUrl = '/api/v1/media/health-education/stream/398254007_hi.opus';

    if (lang == 'or') {
      clipTitle = 'ଗର୍ଭାବସ୍ଥାରେ ସ୍ୱାସ୍ଥ୍ୟ ଏବଂ ବିପଦ ସଙ୍କେତ (୬୦ ସେକେଣ୍ଡ)';
      streamUrl = '/api/v1/media/health-education/stream/398254007_or.opus';
    } else if (lang == 'te') {
      clipTitle = 'గర్భధారణలో ఆరోగ్య జాగ్రత్తలు (60s)';
      streamUrl = '/api/v1/media/health-education/stream/398254007_te.opus';
    }

    cards.add(AshaTriageCard.green(
      title: 'Routine Health Education Counseling',
      subtitle: 'Verified NHM audio guide ready for playback to mother and family.',
      audioEducationUrl: streamUrl,
      audioTitle: clipTitle,
      audioDuration: '60s',
    ));

    return cards;
  }
}
