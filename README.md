# mini-synth

Simple sound synthesiser using pygame and guizero

Other required modules: numpy

## Warning

If you edit the online version of this file, it may conflict with other changes in any checked-out versions.

## Development stages:

1. Make basic waveform generator with sine, triangle, sawtooth and square waves. (Done)

2. Add spaced sawtooth and pulse width control of square wave. (Done)

3. Add screen keyboard. (Done)

4. Make envelope shaper with controllable ADSR function to control tone amplitude. (Done)

5. Storage and recall of synth settings (voices and patches). (Done for voices.)

6. Add tremolo (amplitude wobble), vibrato (frequency wobble) and harmonic boost (fundamental cancellation)
   to all waveforms. (Done)

7. Add sequence/melody editor. (In progress)

8. Make variable lowpass and highpass, bandpass and bandstop filters to modify sound spectrum.

9. Low frequency oscillators for modulating other parameters.

10. Separate envelope shapers for VCF and VCA control.

11. White and pink noise generators, random pitch and amplitude modulation.

12. Stereo panning, ring modulator, phasing, chorus, unison, reverb, resonnance filter module, sub-oscillator,
    quantisation, automatic chords, note length control in sequencer?

13. Spectrum analysis and display? Probably too much processing, except during voice editing perhaps.

14. Algorithmic sequence generation, e.g. using Conways Game of Life?

## Known Bugs / Issues

Changing the voice causes a note to be played several times in response to each parameter that changes. Guizero seems
to respond to the program writing new slider values in the same way as when the user manually moves the slider.

The Model class has copies of some parameters that are in the Controller class. This may be unecessary.

The view and model objects read parameters directly from the controller object. This would make thorough testing
of those modules more difficult as they rely on 'hidden' inputs.

Variables called key and semitone often refer to the same data. This is confusing.

The sustain_level parameter is input as a percentage but used as a factor with maximum value 1.0. This can be
confusing.

Adjusting the envelope parameters and tremolo is laggy because for every detected change the envelope is remade and
a note is played. If a short time delay were added to debounce the inputs the controls could be more responsive. This
requires a timout event which seems to need multiprocessing in the Python program - tricky.

Tremolo rate is fixed for all waveforms, but vibrato is proportional to the tone fundamental frequency.

The tone-tracking notch filter used to produce harmonic boost involves a lot more calculation than the previous production
of a cancellation tone through the sine function. This copes better with vibrato and any future unison function.

The range of the vibrato controls have been arbitrarily set and may not be optimal. Magic numbers could be turned
into undisplayed settings.

All tones are generated 1000 ms long, regardless of the length of any notes using each tone. System RAM could be used more
efficiently.

Different components of a unison may want to be spread out over the stereo field, implying that voices need to be generated
in stereo.

Using 1000 ms tone samples and 1 Hz frequency resolution means that the waveform passes through zero at the start and end. This
could enable the production of notes longer than 1000 ms. Vibrato and unison should not be a problem, if the tones used are
also multiples of 1 Hz.


## Notes

When passing around notes in a sequence, it may be appropriate to group them by timeslot, so that only the information
that is needed for audio production, or for display is being moved around.

The sequence editor could select which voices are to be shown, to allow for multiple voices on the same timeslot and note.

MIDI note numbers from 0 to 127 are a standard for keyboard instruments. 55 Hz is MIDI key 33 and number increases
by 12 every octave.

The number of saved voice settings may be greater than can be handled by the processor at once, so there needs
to be a distinction between active voices and stored voice settings. A configuration file might point to
different settings files, but this creates the possibility of two voices having the same ID but different
parameters.

Different voices may have different pitch ranges and key-to-semitone mappings.

When controlling the VCF from the envelope shaper, a frequency offset linked to the tone fundamental frequency
should perhaps be applied, to give the same kind of tone colour variation in all octaves.

The Elektor Formant uses exponential amplitude control in its Voltage Controlled Amplifier for the main envelope
and linear modulation for tremolo effects.

All notes are currently the same loudness and duration. A more complicated screen KB interface might get around this.
Some synths modify the ADSR length with pitch using "key follow". 

The variable width waveforms have DC offsets which could be a problem in filter circuits using integrators.
Perhaps a DC blocking filter could be used or the offsets could be calculated an removed in the tone generators.

If being used as a sequencer/ pianola, how do note lengths relate to the envelope shape? Is it just the sustain
time that varies?

Can the program structure be modified to make maximum use of a processor with multiple CPU cores? (numpy is
believed to do this automatically for some functions.)

Does the sampled waveform create noticeable pitch/period jitter on square and sawtooth waveforms?

Are there performance limits in the pygame.mixer module that cause pausing during a high note rate? Consider using the
sounddevice module.

If different instruments have different ranges, where should the mapping from key numbers to tone frequencies be done?
Use MIDI key numbers?

For a sequencer, how should note length be adjusted according to changes in tempo.

Portamento-type pitch slides seem incompatible with a wavetable design.

Perhaps envelope control of VCO pitch could be achieved for attack and sustain but not for release, which will move
around with note length. The pitch offset during sustain may be best set to zero anyway. Inversion of ADSR is said to make
for good drum sounds, but is this just due to an effective zero attack time?

Self-oscillation of LPFs can be a positive feature apparently.

Extended LFO rates into the audio range with independent LFO control of VCO and pulse width can produce very complex sounds.

Perceived loudness of short notes is said to less than notes longer than a duration that reduces with increasing pitch.

Real instruments have inharmonicity, where the higher partials are not exact multiples of the fundamental.

Some instruments, e.g. oboe have lower levels of the fundamental than the higher harmonics / partials - see harmonic boost function.

Roland RE201 Space Echo.

In the Serum software synth, one "oscillator" can contain sine, triangle, sawtooth and squre waves in any ratio.

Percussion-type voices do not necessarily need to be controlled by a keyboard.

Scales could be indicated graphically on the sequence editor.

## Background reading:

Elektor magazine "Formant" synthesiser project book. (stored here)

## Contact:

https://en.wikibooks.org/wiki/User_talk:Unkle_Peter
