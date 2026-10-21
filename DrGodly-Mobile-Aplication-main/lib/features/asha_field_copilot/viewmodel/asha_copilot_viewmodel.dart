import 'dart:async';
import 'package:flutter/foundation.dart';
import '../models/asha_household.dart';
import '../models/asha_beneficiary.dart';
import '../models/asha_care_gap.dart';
import '../models/asha_triage_card.dart';
import '../data/asha_local_database.dart';
import '../data/asha_sync_queue_service.dart';
import '../services/asha_voice_recorder_service.dart';
import '../services/asha_ble_poc_bridge.dart';
import '../services/asha_mcp_bridge_service.dart';

/// ViewModel managing state for the low-literacy, voice-first AshaFieldCopilot
class AshaCopilotViewModel extends ChangeNotifier {
  final AshaLocalDatabase _db = AshaLocalDatabase.instance;
  final AshaSyncQueueService _syncQueue = AshaSyncQueueService.instance;
  final AshaVoiceRecorderService _voiceRecorder = AshaVoiceRecorderService();
  final AshaBlePocBridge _bleBridge = AshaBlePocBridge.instance;
  final AshaMcpBridgeService _mcpBridge = AshaMcpBridgeService();

  // State
  String _selectedLanguageCode = 'hi';
  String get selectedLanguageCode => _selectedLanguageCode;

  String _villageLgdCode = '215432';
  String get villageLgdCode => _villageLgdCode;

  List<AshaHousehold> _households = [];
  List<AshaHousehold> get households => _households;

  AshaHousehold? _selectedHousehold;
  AshaHousehold? get selectedHousehold => _selectedHousehold;

  AshaBeneficiary? _selectedBeneficiary;
  AshaBeneficiary? get selectedBeneficiary => _selectedBeneficiary;

  List<AshaCareGap> _householdCareGaps = [];
  List<AshaCareGap> get householdCareGaps => _householdCareGaps;

  List<AshaTriageCard> _triageCards = [];
  List<AshaTriageCard> get triageCards => _triageCards;

  // Active visit telemetry
  Map<String, dynamic> _currentVitals = {};
  Map<String, dynamic> get currentVitals => _currentVitals;

  String _currentTranscript = '';
  String get currentTranscript => _currentTranscript;

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  int _pendingOutboxCount = 0;
  int get pendingOutboxCount => _pendingOutboxCount;

  bool _isEscalated = false;
  bool get isEscalated => _isEscalated;

  StreamSubscription? _pocSub;
  StreamSubscription? _syncSub;

  AshaCopilotViewModel() {
    _init();
  }

  void _init() async {
    // 1. Seed or load households from local SQLite
    await _loadLocalHouseholds();

    // 2. Listen to BLE Point-of-Care device readings
    _pocSub = _bleBridge.readingStream.listen((event) {
      _currentVitals.addAll(event.values);
      notifyListeners();
    });

    // 3. Listen to sync queue outbox updates
    _syncSub = _syncQueue.syncStatusStream.listen((status) {
      _pendingOutboxCount = status['pending_outbox_count'] ?? 0;
      notifyListeners();
    });

    _pendingOutboxCount = await _db.getPendingOutboxCount();
    notifyListeners();
  }

  void setLanguage(String lang) {
    _selectedLanguageCode = lang;
    notifyListeners();
  }

  Future<void> _loadLocalHouseholds() async {
    _isLoading = true;
    notifyListeners();

    var list = await _db.getHouseholdsByVillage(_villageLgdCode);
    if (list.isEmpty) {
      // Seed default rural households for Rampur village (LGD 215432)
      final seedHouseholds = [
        AshaHousehold(
          id: 'group-hh-ward3-42',
          villageLgdCode: _villageLgdCode,
          headName: 'Ramesh Patra',
          address: 'House No. 42, Ward 3, Rampur',
          wardNumber: 'Ward 3',
          contactPhone: '+919876500112',
          memberCount: 4,
          members: const [
            AshaBeneficiary(
              id: 'patient-asha-anita-patra',
              householdId: 'group-hh-ward3-42',
              name: 'Anita Patra',
              gender: 'female',
              ageYears: 24,
              isMaternal: true,
              gestationalWeeks: 32,
              completedAncVisits: 1,
            ),
            AshaBeneficiary(
              id: 'patient-asha-baby-aarav',
              householdId: 'group-hh-ward3-42',
              name: 'Baby Aarav',
              gender: 'male',
              ageYears: 0,
              ageMonths: 6,
              isChild: true,
              receivedVaccines: ['BCG', 'HepB-0', 'OPV-0'],
            ),
            AshaBeneficiary(
              id: 'patient-asha-ramesh-patra',
              householdId: 'group-hh-ward3-42',
              name: 'Ramesh Patra',
              gender: 'male',
              ageYears: 42,
            ),
          ],
        ),
        AshaHousehold(
          id: 'group-hh-ward1-18',
          villageLgdCode: _villageLgdCode,
          headName: 'Bikram Jena',
          address: 'House No. 18, Ward 1, Rampur',
          wardNumber: 'Ward 1',
          contactPhone: '+919876544001',
          memberCount: 3,
          members: const [
            AshaBeneficiary(
              id: 'patient-asha-baby-priya',
              householdId: 'group-hh-ward1-18',
              name: 'Priya Jena',
              gender: 'female',
              ageYears: 1,
              ageMonths: 11,
              isChild: true,
              receivedVaccines: ['BCG', 'OPV-1', 'Pentavalent-1'],
            ),
          ],
        ),
      ];

      await _db.cacheHouseholds(seedHouseholds);

      // Seed care gaps
      final seedGaps = [
        const AshaCareGap(
          id: 'gap-imm-aarav-penta1',
          householdId: 'group-hh-ward3-42',
          patientId: 'patient-asha-baby-aarav',
          patientName: 'Aarav Patra',
          gapType: 'IMMUNIZATION',
          title: 'Pentavalent-1 Overdue',
          description: 'Pentavalent 1 (DPT + HepB + Hib) due at 6 weeks.',
          dueDate: '2026-09-26',
          daysOverdue: 26,
          urgency: 'HIGH',
          action: 'Mobilize for next VHSND.',
        ),
        const AshaCareGap(
          id: 'gap-imm-aarav-rota1',
          householdId: 'group-hh-ward3-42',
          patientId: 'patient-asha-baby-aarav',
          patientName: 'Aarav Patra',
          gapType: 'IMMUNIZATION',
          title: 'Rotavirus-1 Overdue',
          description: 'Rotavirus 1 due for diarrheal prevention.',
          dueDate: '2026-09-26',
          daysOverdue: 26,
          urgency: 'HIGH',
          action: 'Administer oral rotavirus drops.',
        ),
      ];
      await _db.cacheCareGaps(seedGaps);

      list = seedHouseholds;
    }

    _households = list;
    if (_households.isNotEmpty) {
      selectHousehold(_households.first);
    }
    _isLoading = false;
    notifyListeners();
  }

  void selectHousehold(AshaHousehold hh) async {
    _selectedHousehold = hh;
    _selectedBeneficiary = hh.members.firstWhere(
      (m) => m.isMaternal,
      orElse: () => hh.members.isNotEmpty ? hh.members.first : const AshaBeneficiary(
        id: 'patient-unknown',
        householdId: '',
        name: 'Beneficiary',
        gender: 'female',
        ageYears: 25,
      ),
    );

    _householdCareGaps = await _db.getCareGapsForHousehold(hh.id);
    _triageCards = [];
    _currentVitals = {};
    _currentTranscript = '';
    _isEscalated = false;
    notifyListeners();
  }

  void selectBeneficiary(AshaBeneficiary beneficiary) {
    _selectedBeneficiary = beneficiary;
    notifyListeners();
  }

  /// Start voice recording visit
  Future<void> startVoiceVisit() async {
    await _voiceRecorder.startListening(languageCode: _selectedLanguageCode);
    notifyListeners();
  }

  /// Stop voice recording, transcribe & evaluate via MCP
  Future<void> stopVoiceVisit() async {
    final isMaternal = _selectedBeneficiary?.isMaternal ?? true;
    final transcript = await _voiceRecorder.stopListeningAndTranscribe(
      languageCode: _selectedLanguageCode,
      isMaternal: isMaternal,
    );

    _currentTranscript = transcript;

    // Simulate auto-captured vitals from dialogue if not yet captured via BLE
    if (!_currentVitals.containsKey('systolic_bp')) {
      _currentVitals['systolic_bp'] = 146.0;
      _currentVitals['diastolic_bp'] = 96.0;
      _currentVitals['hemoglobin'] = 6.6;
    }

    // Call MCP Bridge to generate traffic light cards
    _triageCards = await _mcpBridge.generateTriageCards(
      patientId: _selectedBeneficiary?.id ?? 'patient-default',
      transcript: transcript,
      vitals: _currentVitals,
      activeCareGaps: _householdCareGaps,
      isMaternal: isMaternal,
      languageCode: _selectedLanguageCode,
    );

    // Enqueue visit to offline outbox
    await _enqueueCurrentVisit();

    notifyListeners();
  }

  /// 1-Tap Escalate to PHC
  Future<void> escalateToPhc() async {
    _isEscalated = true;
    notifyListeners();

    // Trigger urgent outbox escalation
    final visitUuid = 'urg-esc-${DateTime.now().millisecondsSinceEpoch}';
    await _syncQueue.enqueueVisitSync(
      visitUuid: visitUuid,
      visitPayload: {
        'patient_id': _selectedBeneficiary?.id,
        'worker_id': 'usr-asha-sunita',
        'village_lgd_code': _villageLgdCode,
        'encounter_type': 'emergency_escalation',
        'is_high_risk': true,
        'triage_category': 'HIGH_PRIORITY_PHC_REFERRAL',
        'vitals': _currentVitals,
        'transcript': _currentTranscript,
      },
    );
  }

  /// Manually pair or inject BLE PoC reading
  void injectPocReading(String type, Map<String, dynamic> values) {
    _bleBridge.injectSimulatedReading(PocReadingEvent(
      deviceType: type,
      values: values,
      deviceName: 'Field Kit Bluetooth Device',
      timestamp: DateTime.now().toUtc().toIso8601String(),
    ));
  }

  Future<void> _enqueueCurrentVisit() async {
    final visitUuid = 'visit-${DateTime.now().millisecondsSinceEpoch}';
    final isHighRisk = _triageCards.any((c) => c.light == TriageTrafficLight.red);

    await _syncQueue.enqueueVisitSync(
      visitUuid: visitUuid,
      visitPayload: {
        'patient_id': _selectedBeneficiary?.id,
        'worker_id': 'usr-asha-sunita',
        'village_lgd_code': _villageLgdCode,
        'encounter_type': (_selectedBeneficiary?.isMaternal ?? false) ? 'anc_home_visit' : 'household_visit',
        'is_high_risk': isHighRisk,
        'triage_category': isHighRisk ? 'EMERGENCY_REFERRAL' : 'ROUTINE',
        'vitals': _currentVitals,
        'transcript': _currentTranscript,
      },
    );
  }

  @override
  void dispose() {
    _pocSub?.cancel();
    _syncSub?.cancel();
    _voiceRecorder.dispose();
    super.dispose();
  }
}
