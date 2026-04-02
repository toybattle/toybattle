using Microsoft.Win32;

namespace ToyBatlleLauncher
{
    public class RegistryHelper
    {
        private const string RegistryPath = @"SOFTWARE\ToyBattle";

        public RegistryHelper() { }
        
        public static bool SaveValue(string keyName, string value, bool useCurrentUser = true) 
        {
            try
            {
                RegistryKey baseKey = useCurrentUser ? Registry.CurrentUser : Registry.LocalMachine;
                using (RegistryKey key = baseKey.CreateSubKey(RegistryPath))
                {
                    if (key != null)
                    {
                        key.SetValue(keyName, value);
                        return true;
                    }
                }
            }
            catch (Exception ex) 
            { 
                Console.WriteLine($"Erreur lors de la sauvgarde {ex.Message}");
            }
            return false;
        }

        public static string LoadValue(string keyName, bool useCurrentUser = true)
        {
            try
            {
                RegistryKey baseKey = useCurrentUser ? Registry.CurrentUser : Registry.LocalMachine;
                using (RegistryKey key = baseKey.OpenSubKey(RegistryPath))
                {
                    if (key != null)
                    {
                        object value = key.GetValue(keyName);
                        if(value != null)
                        {
                            return value.ToString();
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Erreur lors du chargement {ex.Message}");
            }
            return string.Empty;
        }

        public static bool DeleteValue(string keyName, bool useCurrentUser = true)
        {
            try
            {
                RegistryKey baseKey = useCurrentUser ? Registry.CurrentUser : Registry.LocalMachine;
                using (RegistryKey key = baseKey.OpenSubKey(RegistryPath, true))
                {
                    if (key != null && key.GetValue(keyName) != null)
                    {
                        key.DeleteSubKey(keyName);
                        return true;
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Erreur lors de la suppersion {ex.Message}");
            }
            return false;
        }

        public static bool CheckExistValue(string keyName, bool useCurrentUser = true)
        {
            try
            {
                RegistryKey baseKey = useCurrentUser ? Registry.CurrentUser : Registry.LocalMachine;
                using (RegistryKey key = baseKey.OpenSubKey(RegistryPath, true))
                {
                    if (key != null && key.GetValue(keyName) != null)
                    {
                        return true;
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Erreur lors de la suppersion {ex.Message}");
            }
            return false;
        }
    }
}
