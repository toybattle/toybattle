using System;
using System.Diagnostics;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Media.Imaging;

namespace ToyBatlleLauncher
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window
    {
        private DataBase dataBase;
        private GameUpdateManager gameManager;
        private TaskCompletionSource<bool>? _confirmTcs;

        private bool isSignUp = false;
        private bool _isUpdateCancelled = false;

        public MainWindow()
        {
            InitializeComponent();
            dataBase = new DataBase();
            Loaded += async (s, e) => {
                await dataBase.InitializeAsync();
                UpdateUI();
            };
            this.Loaded += MainWindow_Loaded;
        }

        private async void MainWindow_Loaded(object sender, RoutedEventArgs e)
        {
            gameManager = new GameUpdateManager();

            if (!gameManager.IsGameInstalled())
            {
                bool result = await ShowConfirmOverlay("Installation", "Le jeu n'est pas installé. Voulez-vous l'installer maintenant ?");

                if (result)
                {
                    await InstallGameAsync();
                }
            }
            else
            {
                await CheckGameUpdatesAsync();
            }

            Email_TextBox.Text = RegistryHelper.LoadValue("email");
            Username_TextBox.Text = RegistryHelper.LoadValue("username");
            Password_TextBox.Text = RegistryHelper.LoadValue("password");
        }

        private async Task InstallGameAsync()
        {
            GameUpdateInfo updateInfo = await gameManager.CheckForGameUpdatesAsync();

            if (updateInfo != null)
            {
                ShowProgressOverlay("Installation initiale du jeu...");

                var progress = new Progress<double>(p => UpdateUpdateProgress(p));

                bool success = await gameManager.DownloadGameUpdateAsync(updateInfo, progress);

                if (success)
                {
                    await ShowSummaryOverlay("Installation Terminée", "Le jeu a été installé avec succès ! Vous pouvez maintenant le lancer.");
                }
                else
                {
                    HideOverlay();
                }
            }
            else
            {
                await ShowSummaryOverlay("Erreur", "Impossible de récupérer les informations d'installation.");
            }
        }

        private async Task CheckGameUpdatesAsync()
        {
            GameUpdateInfo updateInfo = await gameManager.CheckForGameUpdatesAsync();

            if (updateInfo != null)
            {
                bool result = await ShowConfirmOverlay("Mise à jour disponible", 
                    $"Une nouvelle version du jeu ({updateInfo.Version}) est disponible !\n\n" +
                    $"Changements :\n{updateInfo.Changelog}\n\n" +
                    $"Voulez-vous mettre à jour maintenant ?");

                if (result)
                {
                    ShowProgressOverlay($"Mise à jour vers la version {updateInfo.Version}...");

                    var progress = new Progress<double>(p => UpdateUpdateProgress(p));

                    bool success = await gameManager.DownloadGameUpdateAsync(updateInfo, progress);

                    if (success)
                    {
                        await ShowSummaryOverlay("Mise à jour Réussie", 
                            $"Le jeu a été mis à jour vers la version {updateInfo.Version}.\n\n" +
                            $"Changements :\n{updateInfo.Changelog}");
                    }
                    else
                    {
                        HideOverlay();
                    }
                }
            }
        }

        private async void CheckUpdatesButton_Click(object sender, RoutedEventArgs e)
        {
            await CheckGameUpdatesAsync();
        }

        private async void Action_Button_Click(object sender, RoutedEventArgs e)
        {
            if (isSignUp)
            {
                await Sign_Up();
            }
            else
            {
                await Sign_In();
            }
        }

        private async Task Sign_Up()
        {
            string email = Email_TextBox.Text;
            string password = Password_TextBox.Text;
            string username = Username_TextBox.Text;

            bool success = await dataBase.Sign_Up_Async(email, password, username);
            if (success)
            {
                RegistryHelper.SaveValue("email", email);
                RegistryHelper.SaveValue("username", username);
                RegistryHelper.SaveValue("password", password);

                await ShowSummaryOverlay("Succès", "Inscription réussie !");
            }
            else
            {
                await ShowSummaryOverlay("Erreur", "Erreur lors de l'inscription.");
            }
        }

        private async Task Sign_In()
        {
            string email = Email_TextBox.Text;
            string password = Password_TextBox.Text;
            string username = Username_TextBox.Text;

            bool success = await dataBase.Sign_In_Async(email, password);
            if (success)
            {
                if(!RegistryHelper.CheckExistValue("email") || !RegistryHelper.CheckExistValue("username") || !RegistryHelper.CheckExistValue("password"))
                {
                    RegistryHelper.SaveValue("email", email);
                    RegistryHelper.SaveValue("username", username);
                    RegistryHelper.SaveValue("password", password);
                }
                gameManager.LaunchGame();
                Application.Current.Shutdown();
            }
            else
            {
                await ShowSummaryOverlay("Erreur", "Erreur lors de la connexion. Vérifiez vos identifiants.");
            }
        }

        private void Switch_Sign_Up_Button_Click(object sender, RoutedEventArgs e)
        {
            isSignUp = !isSignUp;
            UpdateUI();
        }

        private void UpdateUI()
        {
            if (isSignUp)
            {
                background_Image.ImageSource = new BitmapImage(new Uri("assets/sign_up_empty_input.png", UriKind.Relative));
                Username_TextBox.Text = "Username";
                Email_TextBox.Text = "Email";
                Password_TextBox.Text = "Password";
            }
            else
            {
                background_Image.ImageSource = new BitmapImage(new Uri("assets/sign_in_empty_input.png", UriKind.Relative));
                Email_TextBox.Text = RegistryHelper.LoadValue("email");
                Username_TextBox.Text = RegistryHelper.LoadValue("username");
                Password_TextBox.Text = RegistryHelper.LoadValue("password");
            }
        }

        #region Overlay Logic
        private void HideOverlay()
        {
            MainOverlay.Visibility = Visibility.Collapsed;
            ConfirmPanel.Visibility = Visibility.Collapsed;
            ProgressPanel.Visibility = Visibility.Collapsed;
            SummaryPanel.Visibility = Visibility.Collapsed;
            ActionButton.IsEnabled = true;
            SwitchButton.IsEnabled = true;
        }

        private async Task<bool> ShowConfirmOverlay(string title, string message)
        {
            HideOverlay();
            OverlayTitle.Text = title;
            ConfirmMessage.Text = message;
            ConfirmPanel.Visibility = Visibility.Visible;
            MainOverlay.Visibility = Visibility.Visible;
            ActionButton.IsEnabled = false;
            SwitchButton.IsEnabled = false;

            _confirmTcs = new TaskCompletionSource<bool>();
            return await _confirmTcs.Task;
        }

        private void ShowProgressOverlay(string title)
        {
            HideOverlay();
            _isUpdateCancelled = false;
            OverlayTitle.Text = title;
            UpdateProgressBar.Value = 0;
            UpdateProgressText.Text = "0%";
            ProgressPanel.Visibility = Visibility.Visible;
            MainOverlay.Visibility = Visibility.Visible;
            ActionButton.IsEnabled = false;
            SwitchButton.IsEnabled = false;
        }

        private async Task ShowSummaryOverlay(string title, string summary)
        {
            HideOverlay();
            OverlayTitle.Text = title;
            SummaryText.Text = summary;
            SummaryPanel.Visibility = Visibility.Visible;
            MainOverlay.Visibility = Visibility.Visible;
            ActionButton.IsEnabled = false;
            SwitchButton.IsEnabled = false;

            _confirmTcs = new TaskCompletionSource<bool>();
            await _confirmTcs.Task;
        }

        private void ConfirmYesButton_Click(object sender, RoutedEventArgs e)
        {
            _confirmTcs?.TrySetResult(true);
        }

        private void ConfirmNoButton_Click(object sender, RoutedEventArgs e)
        {
            HideOverlay();
            _confirmTcs?.TrySetResult(false);
        }

        private void SummaryCloseButton_Click(object sender, RoutedEventArgs e)
        {
            HideOverlay();
            _confirmTcs?.TrySetResult(true);
        }

        public void UpdateUpdateProgress(double percent)
        {
            Dispatcher.Invoke(() =>
            {
                UpdateProgressBar.Value = percent;
                UpdateProgressText.Text = $"{percent:F1}%";

                if (percent >= 100)
                {
                    UpdateProgressText.Text = "Téléchargement terminé ! Installation en cours...";
                }
            });
        }

        private async void CancelUpdateButton_Click(object sender, RoutedEventArgs e)
        {
            _isUpdateCancelled = true;
            await ShowSummaryOverlay("Annulation", "Téléchargement annulé par l'utilisateur.");
        }
        #endregion
    }
}