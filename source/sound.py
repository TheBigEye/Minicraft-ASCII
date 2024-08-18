import pygame

class Sound:
    sounds = {}

    @staticmethod
    def initialize():
        pygame.mixer.init(44100, 16, 2, 4096)

        # List of sounds to load
        sound_files = {
            'playerHurt': './assets/sounds/playerHurt.ogg',
            'genericHurt': './assets/sounds/genericHurt.ogg',
            'confirmSound': './assets/sounds/confirmSound.ogg',
            'eventSound': './assets/sounds/eventSound.ogg',
            'spawnSound': './assets/sounds/spawnSound.ogg',
            'typingSound': './assets/sounds/typingSound.ogg'
        }

        # Load all sounds into the dictionary
        for key, file_path in sound_files.items():
            Sound.sounds[key] = pygame.mixer.Sound(file_path)

    @staticmethod
    def play(sound_name: str):
        if sound_name in Sound.sounds:
            Sound.sounds[sound_name].play()
        else:
            print(f"[PLAY] Sound '{sound_name}' not found!")

    @staticmethod
    def stop(sound_name: str):
        if sound_name in Sound.sounds:
            Sound.sounds[sound_name].stop()
        else:
            print(f"[STOP] Sound '{sound_name}' not found!")
