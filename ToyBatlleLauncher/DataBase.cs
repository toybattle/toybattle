using Supabase;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ToyBatlleLauncher
{
    public class DataBase
    {
        private readonly Client _client;

        public DataBase()
        {
            var url = "https://okvqvwpnlzkjquwliuhy.supabase.co";
            var apikey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9rdnF2d3BubHpranF1d2xpdWh5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM1MDgxNTIsImV4cCI6MjA4OTA4NDE1Mn0.qHIL64t-54JljDrCoX5QD4qgpMeOwCp83GtXcJdJpwc";

            var options = new SupabaseOptions
            {
                AutoRefreshToken = true,
                AutoConnectRealtime = false
            };

            _client = new Client(url, apikey, options);
        }

        public async Task InitializeAsync()
        {
            await _client.InitializeAsync();
        }

        public async Task<bool> Sign_In_Async(string email, string password)
        {
            try
            {
                var session = await _client.Auth.SignIn(email, password);

                if (session != null && session.User != null) return true;
                return false;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Erreur connection: {ex.Message}");
                return false;
            }
        }

        public async Task<bool> Sign_Up_Async(string email, string password, string username)
        {
            try
            {
                var metadata = new Dictionary<string, object>
                {
                    {"displayName", username }
                };

                var option = new Supabase.Gotrue.SignUpOptions
                {
                    Data = metadata
                };

                var session = await _client.Auth.SignUp(email, password, option);

                if (session != null && session.User != null) return true;
                return false;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Erreur connection: {ex.Message}");
                return false;
            }
        }

        public bool IsSign_In()
        {
            return _client.Auth.CurrentUser != null;
        }

        public async Task Sign_Out()
        {
            await _client.Auth.SignOut();
        }
    }
}
