/**
 * Text-to-Speech Hook - Enhanced Version
 * Uses browser's Web Speech API with better voice selection
 */
import { useState, useCallback, useEffect, useRef } from 'react';

export function useTextToSpeech() {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const [voices, setVoices] = useState([]);
  const selectedVoice = useRef(null);

  // Load available voices
  useEffect(() => {
    if (!('speechSynthesis' in window)) {
      setIsSupported(false);
      return;
    }

    setIsSupported(true);

    const loadVoices = () => {
      const availableVoices = window.speechSynthesis.getVoices();
      setVoices(availableVoices);
      
      if (availableVoices.length > 0) {
        // Priority order for natural-sounding voices
        const voicePreferences = [
          // Google voices (best quality)
          (v) => v.name.includes('Google') && v.lang.startsWith('en'),
          // Microsoft natural voices
          (v) => v.name.includes('Natural') && v.lang.startsWith('en'),
          (v) => v.name.includes('Microsoft') && v.name.includes('Online') && v.lang.startsWith('en'),
          // Apple voices
          (v) => v.name.includes('Samantha'),
          (v) => v.name.includes('Karen'),
          (v) => v.name.includes('Daniel'),
          // Any premium/enhanced voice
          (v) => v.name.includes('Premium') && v.lang.startsWith('en'),
          (v) => v.name.includes('Enhanced') && v.lang.startsWith('en'),
          // Female voices often sound clearer
          (v) => v.name.includes('Female') && v.lang.startsWith('en'),
          (v) => v.name.includes('Zira') && v.lang.startsWith('en'),
          (v) => v.name.includes('Hazel') && v.lang.startsWith('en'),
          // Any English voice
          (v) => v.lang.startsWith('en-US'),
          (v) => v.lang.startsWith('en-GB'),
          (v) => v.lang.startsWith('en'),
        ];

        // Find the best available voice
        for (const preference of voicePreferences) {
          const voice = availableVoices.find(preference);
          if (voice) {
            selectedVoice.current = voice;
            console.log('🔊 Selected voice:', voice.name);
            break;
          }
        }

        // Fallback to first English voice or any voice
        if (!selectedVoice.current) {
          selectedVoice.current = availableVoices.find(v => v.lang.startsWith('en')) 
            || availableVoices[0];
        }
      }
    };

    // Load voices immediately if available
    loadVoices();

    // Chrome needs this event to load voices
    window.speechSynthesis.onvoiceschanged = loadVoices;

    return () => {
      window.speechSynthesis.onvoiceschanged = null;
    };
  }, []);

  const speak = useCallback((text) => {
    if (!isSupported) {
      console.warn('Text-to-speech not supported in this browser');
      return;
    }

    // Cancel any ongoing speech
    window.speechSynthesis.cancel();

    // Clean up text for better speech
    const cleanText = text
      .replace(/[😊😐😷🤢🤮☠️🚨💡⚠️]/g, '') // Remove emojis
      .replace(/AQI/g, 'A Q I')  // Spell out AQI
      .replace(/°C/g, ' degrees Celsius')
      .replace(/°F/g, ' degrees Fahrenheit')
      .replace(/%/g, ' percent')
      .replace(/\s+/g, ' ') // Normalize whitespace
      .trim();

    const utterance = new SpeechSynthesisUtterance(cleanText);
    
    // Configure voice settings for more natural sound
    utterance.rate = 0.95;   // Slightly slower than default (0.1 - 10, default 1)
    utterance.pitch = 1.0;   // Normal pitch (0 - 2, default 1)
    utterance.volume = 1.0;  // Full volume (0 - 1)
    
    // Use selected voice
    if (selectedVoice.current) {
      utterance.voice = selectedVoice.current;
    }

    // Event handlers
    utterance.onstart = () => {
      setIsSpeaking(true);
    };

    utterance.onend = () => {
      setIsSpeaking(false);
    };

    utterance.onerror = (event) => {
      console.error('Speech error:', event.error);
      setIsSpeaking(false);
    };

    // Chrome bug fix: speech can get stuck, so we need to resume periodically
    const resumeInterval = setInterval(() => {
      if (window.speechSynthesis.paused) {
        window.speechSynthesis.resume();
      }
    }, 1000);

    utterance.onend = () => {
      clearInterval(resumeInterval);
      setIsSpeaking(false);
    };

    utterance.onerror = () => {
      clearInterval(resumeInterval);
      setIsSpeaking(false);
    };

    window.speechSynthesis.speak(utterance);
  }, [isSupported]);

  const stop = useCallback(() => {
    if (isSupported) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  }, [isSupported]);

  // Get list of available voices (for debugging/settings)
  const getVoices = useCallback(() => {
    return voices.map(v => ({
      name: v.name,
      lang: v.lang,
      local: v.localService,
    }));
  }, [voices]);

  return { 
    speak, 
    stop, 
    isSpeaking, 
    isSupported,
    getVoices,
    currentVoice: selectedVoice.current?.name || 'Default'
  };
}

export default useTextToSpeech;