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

6. Add tremolo (amplitude wobble) and vibrato (frequency wobble) to all waveforms. (Under way)

7. Make variable lowpass and highpass, bandpass and bandstop filters to modify sound spectrum.

8. Low frequency oscillators for modulating other parameters.

9. Separate envelope shapers for VCF and VCA control.

9. White and pink noise generators, random pitch and amplitude modulation.

10. Ring modulator, phasing, chorus, unison, reverb, resonnance filter module?

11. Melody recording and editing?

12. Spectrum analysis and display? Probably too much processing, except during voice editing perhaps.

13. Algorithmic sequence generation, e.g. using Conways Game of Life?

## Known Bugs / Issues

The Model class has copies of some parameters that are in the Voice class. This may be unecessary.

The function to rebuild the voices for all tones after a parameter change is quite slow and could perhaps
be done more on a just-in-time basis. e.g. just rebuild the current tone and do the others while the sample
tone is being played.

The view and model objects read voice parameters directly from the controller object. Is this bad practice?

Variables called key and semitone often refer to the same data. This is confusing.

The sustain_level parameter is input as a percentage but used as a factor with maximum value 1.0. This can be
confusing.

Dual display of tone and evelope would be better.

Tremolo rate is fixed for all waveforms, but vibrato is proportional to the tone fundamental frequency.

The range of the vibrato controls have been arbitrarily set and may not be optimal.

Perceived loudness of short notes is said to less than notes longer than a duration that reduces with increasing pitch.

Real instruments have inharmonicity, where the higher partials are not exact multiples of the fundamental.

Some instruments, e.g. oboe have lower levels of the fundamental than the higher harmonics / partials.


## Notes

MIDI note numbers from 0 to 127 are a standard for keyboard instruments. 55 Hz is MIDI key 33 and number increases
by 12 every octave.

The number of saved voice settings may be greater than can be handled by the processor at once, so there needs
to be a distinction between active voices and stored voice settings. A configuration file might point to
different settings files, but this creates the possibility of two voices having the same ID but different
parameters.

Different voices may have different pitch ranges and key to semitone mappings.

When controlling the VCF from the envelope shaper, a frequency offset linked to the tone fundamental frequency
should perhaps be applied, to give the same kind of tone colour variation in all octaves.

The Elektor Formant uses exponential amplitude control in its Voltage Controlled Amplifier for the main envelope
and linear modulation for tremolo effects.

Vibrato effect may be produced in waveform generation functions by adding periodic time offsets to the
sample times arrays.

All notes are currently the same loudness and duration. A more complicated screen KB interface might get around this.
Some synths modify the ADSR length with pitch using "key follow". 

The variable width waveforms have DC offsets which could be a problem in filter circuits using integrators.
Perhaps a DC blocking filter could be used or the offsets could be calculated an removed in the tone generators.

If being used as a sequencer/ pianola, how do note lengths relate to the envelope shape? Is it just the sustain
time that varies?

Can the program structure be modified to make maximum use of a processor with multiple CPU cores? (numpy is
believed to do this automatically for some functions.)

Does the sampled waveform create noticeable pitch/period jitter on square and sawtooth waveforms?

Are there performance limits in the pygame.mixer module that cause pausing during a high note rate?

If different instruments have different ranges, where should the mapping from key numbers to tone frequencies be done?
Use MIDI key numbers?

For a sequencer, how should note length be adjusted according to changes in tempo.

Portamento-type pitch slides seem incompatible with a wavetable design.

Perhaps envelope control of VCO pitch could be achieved for attack and sustain but not for release, which will move
around with note length. The pitch offset during sustain may be best set to zero anyway. Inversion of ADSR is said to make
for good drum sounds, but is this just due to an effective zero attack time?

Self-oscillation of LPFs can be a positive feature apparently.

Extended LFO rates into the audio range with independent LFO control of VCO and pulse width can produce very complex sounds.

Stereo panning, ring modulation.

Roland RE201 Space Echo.

## Background reading:

Elektor magazine "Formant" synthesiser project book. (stored here)

## Contact:

https://en.wikibooks.org/wiki/User_talk:Unkle_Peter
