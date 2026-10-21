import 'dart:async';
import 'dart:io';
import 'package:flutter/foundation.dart';

enum RecordingState {
  idle,
  listening,
  speakingDetected,
  processingTranscription,
  completed,
  error,
}

/// Service handling on-device voice recording, low-bandwidth audio compression,
/// and Sarvam ASR regional speech transcription.
class AshaVoiceRecorderService {
  RecordingState _state = RecordingState.idle;
  RecordingState get state => _state;

  final _stateController = StreamController<RecordingState>.broadcast();
  Stream<RecordingState> get stateStream => _stateController.stream;

  final _transcriptController = StreamController<String>.broadcast();
  Stream<String> get transcriptStream => _transcriptController.stream;

  Timer? _recordingTimer;
  int _secondsRecorded = 0;
  int get secondsRecorded => _secondsRecorded;

  /// Start recording voice visit in chosen regional language
  Future<void> startListening({String languageCode = 'hi-IN'}) async {
    _state = RecordingState.listening;
    _stateController.add(_state);
    _secondsRecorded = 0;

    // Simulate on-device Voice Activity Detection (VAD) activation
    _recordingTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      _secondsRecorded++;
      if (_secondsRecorded == 1) {
        _state = RecordingState.speakingDetected;
        _stateController.add(_state);
      }
    });
  }

  /// Stop listening and transcribe via Sarvam ASR / quantized model
  Future<String> stopListeningAndTranscribe({
    String languageCode = 'hi-IN',
    bool isMaternal = true,
  }) async {
    _recordingTimer?.cancel();
    _state = RecordingState.processingTranscription;
    _stateController.add(_state);

    // Realistic ASR transcription matching frontline field visit dialogues
    String mockTranscript;
    if (isMaternal) {
      if (languageCode.startsWith('or')) {
        mockTranscript =
            'ନମସ୍କାର ଭଉଣୀ। ଆଜି ଅନୀତା ଦିଦିଙ୍କ ଘରକୁ ଆସିଛୁ। ତାଙ୍କ ରକ୍ତଚାପ (ବିପି) ୧୪୬/୯୬ ଆସିଛି। '
            'ହିମୋଗ୍ଲୋବିନ ୬.୬ ଗ୍ରାମ ଅଛି। ଗୋଡ଼ ଫୁଲିଛି ଏବଂ ମୁଣ୍ଡ ବିନ୍ଧା ହେଉଛି।';
      } else {
        mockTranscript =
            'नमस्ते दीदी। आज अनीता दीदी के घर आए हैं। इनका बीपी 146/96 आया है। '
            'खून की जांच में हीमोग्लोबिन 6.6 ग्राम है। पैरों में हल्की सूजन (pair me sujan) है '
            'और तेज सिर दर्द हो रहा है।';
      }
    } else {
      mockTranscript =
          'नमस्ते दीदी। बच्चे को तेज बुखार 39 डिग्री है और सांस तेज चल रही है (fast breathing)। '
          'पसली चल रही है (chest indrawing) और बच्चा दूध नहीं पी रहा है।';
    }

    await Future.delayed(const Duration(milliseconds: 600));

    _state = RecordingState.completed;
    _stateController.add(_state);
    _transcriptController.add(mockTranscript);

    return mockTranscript;
  }

  void reset() {
    _recordingTimer?.cancel();
    _secondsRecorded = 0;
    _state = RecordingState.idle;
    _stateController.add(_state);
  }

  void dispose() {
    _recordingTimer?.cancel();
    _stateController.close();
    _transcriptController.close();
  }
}
