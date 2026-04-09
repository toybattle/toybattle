using System;
using System.IO;
using System.Windows.Media;

namespace ToyBatlleLauncher
{
    public static class MusicManager
    {
        private static MediaPlayer _mediaPlayer = new MediaPlayer();
        private static string? _currentFilePath;

        public static void PlayBackgroundMusic(string filePath)
        {
            if (_currentFilePath == filePath) return;

            try
            {
                string fullPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, filePath);
                if (File.Exists(fullPath))
                {
                    _currentFilePath = filePath;
                    _mediaPlayer.Open(new Uri(fullPath));
                    _mediaPlayer.MediaEnded -= OnMediaEnded; // Ensure no double-subscription
                    _mediaPlayer.MediaEnded += OnMediaEnded;
                    _mediaPlayer.Play();
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error playing music: {ex.Message}");
            }
        }

        private static void OnMediaEnded(object? sender, EventArgs e)
        {
            _mediaPlayer.Position = TimeSpan.Zero;
            _mediaPlayer.Play();
        }

        public static void StopBackgroundMusic()
        {
            _mediaPlayer.Stop();
            _currentFilePath = null;
        }

        public static void SetVolume(double volume)
        {
            _mediaPlayer.Volume = volume;
        }
    }
}
