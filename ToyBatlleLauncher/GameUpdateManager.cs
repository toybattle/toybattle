using System;
using System.IO;
using System.Net.Http;
using System.Threading.Tasks;
using System.Text.Json;
using System.IO.Compression;
using System.Collections.Generic;
using System.Linq;

public class GameUpdateInfo
{
    public string Version { get; set; }
    public string DownloadUrl { get; set; }
    public string Url { get; set; }
    public string Download_url { get; set; }
    public string Link { get; set; }
    public string File_url { get; set; }
    public string FileName { get; set; }
    public string Changelog { get; set; }

    public string GetEffectiveUrl()
    {
        return DownloadUrl ?? Url ?? Download_url ?? Link ?? File_url;
    }
}

public class GameUpdateManager
{
    private const string UPDATE_URL = "https://www.dropbox.com/scl/fi/zbt5lqw2p6mmg6zi8dbxt/update.json?rlkey=jbkexdfiuc10isn157h326lkh&st=9c844otl&dl=1";
    private string gamePath;

    public GameUpdateManager()
    {
        gamePath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "Game", "ToyBattle");

        if (!Directory.Exists(gamePath))
        {
            Directory.CreateDirectory(gamePath);
        }
    }

    public string GetCurrentGameVersion()
    {
        string versionFile = Path.Combine(gamePath, "version.txt");

        if (File.Exists(versionFile))
        {
            return File.ReadAllText(versionFile).Trim();
        }

        return "0.0.0";
    }

    public bool IsGameInstalled()
    {
        string gameExe = Path.Combine(gamePath, "ToyBattle.exe");
        return File.Exists(gameExe);
    }

    public async Task<GameUpdateInfo> CheckForGameUpdatesAsync()
    {
        try
        {
            using (HttpClient client = new HttpClient())
            {
                client.Timeout = TimeSpan.FromSeconds(10);
                string json = await client.GetStringAsync(UPDATE_URL);
                var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
                GameUpdateInfo updateInfo = null;

                try
                {
                    updateInfo = JsonSerializer.Deserialize<GameUpdateInfo>(json, options);
                }
                catch
                {
                    try
                    {
                        var list = JsonSerializer.Deserialize<List<GameUpdateInfo>>(json, options);
                        updateInfo = list?.FirstOrDefault();
                    }
                    catch { }
                }

                if (updateInfo == null) return null;

                string currentVersion = GetCurrentGameVersion();

                if (IsNewerVersion(updateInfo.Version, currentVersion))
                {
                    return updateInfo;
                }
            }
        }
        catch
        {
            // Error handling delegated to caller
        }

        return null; 
    }

    private bool IsNewerVersion(string remoteVersion, string localVersion)
    {
        try
        {
            Version remote = new Version(remoteVersion);
            Version local = new Version(localVersion);
            return remote > local;
        }
        catch
        {
            return remoteVersion != localVersion;
        }
    }

    public async Task<bool> DownloadGameUpdateAsync(GameUpdateInfo updateInfo, IProgress<double> progress)
    {
        try
        {
            string downloadUrl = updateInfo.GetEffectiveUrl();
            if (!string.IsNullOrEmpty(downloadUrl) && !Uri.IsWellFormedUriString(downloadUrl, UriKind.Absolute))
            {
                Uri baseUri = new Uri(UPDATE_URL);
                downloadUrl = new Uri(baseUri, downloadUrl).AbsoluteUri;
            }

            if (string.IsNullOrEmpty(downloadUrl))
            {
                return false;
            }

            string fileName = updateInfo.FileName;
            if (string.IsNullOrEmpty(fileName))
            {
                try
                {
                    if (!string.IsNullOrEmpty(downloadUrl))
                    {
                        fileName = Path.GetFileName(new Uri(downloadUrl).LocalPath);
                    }
                }
                catch { }

                if (string.IsNullOrEmpty(fileName))
                {
                    fileName = "ToyBattle.zip";
                }
            }

            string tempFile = Path.Combine(Path.GetTempPath(), fileName);

            using (HttpClient client = new HttpClient())
            {
                using (HttpResponseMessage response = await client.GetAsync(
                    downloadUrl, HttpCompletionOption.ResponseHeadersRead))
                {
                    response.EnsureSuccessStatusCode();

                    long totalBytes = response.Content.Headers.ContentLength ?? -1;
                    long receivedBytes = 0;

                    using (Stream contentStream = await response.Content.ReadAsStreamAsync())
                    using (FileStream fileStream = new FileStream(tempFile, FileMode.Create, FileAccess.Write, FileShare.None, 8192, true))
                    {
                        byte[] buffer = new byte[8192];
                        int bytesRead;

                        while ((bytesRead = await contentStream.ReadAsync(buffer, 0, buffer.Length)) > 0)
                        {
                            await fileStream.WriteAsync(buffer, 0, bytesRead);
                            receivedBytes += bytesRead;

                            if (totalBytes > 0)
                            {
                                double percent = (double)receivedBytes / totalBytes * 100;
                                progress.Report(percent);
                            }
                        }
                    }
                }
            }

            return await ApplyGameUpdateAsync(tempFile, updateInfo);
        }
        catch
        {
            return false;
        }
    }

    private async Task<bool> ApplyGameUpdateAsync(string updateFile, GameUpdateInfo updateInfo)
    {
        try
        {
            string backupPath = Path.Combine(gamePath, "Backup_" + DateTime.Now.ToString("yyyyMMdd_HHmmss"));

            if (Directory.Exists(backupPath))
                Directory.Delete(backupPath, true);

            string tempExtractPath = Path.Combine(Path.GetTempPath(), "GameUpdateExtract");

            if (Directory.Exists(tempExtractPath))
                Directory.Delete(tempExtractPath, true);
            Directory.CreateDirectory(tempExtractPath);

            ZipFile.ExtractToDirectory(updateFile, tempExtractPath, true);

            if (Directory.Exists(gamePath) && Directory.GetFiles(gamePath).Length > 0)
            {
                Directory.CreateDirectory(backupPath);
                foreach (string file in Directory.GetFiles(gamePath))
                {
                    File.Copy(file, Path.Combine(backupPath, Path.GetFileName(file)), true);
                }
            }

            // Cleanup gamePath (excluding backups)
            foreach (string file in Directory.GetFiles(gamePath))
            {
                File.Delete(file);
            }
            foreach (string dir in Directory.GetDirectories(gamePath))
            {
                if (!Path.GetFileName(dir).StartsWith("Backup_"))
                {
                    Directory.Delete(dir, true);
                }
            }

            // Move extracted files
            string actualSource = tempExtractPath;
            string[] subDirs = Directory.GetDirectories(tempExtractPath);
            string[] levelFiles = Directory.GetFiles(tempExtractPath);

            // "Unwrap" if zip has a single folder
            if (subDirs.Length == 1 && levelFiles.Length == 0)
            {
                actualSource = subDirs[0];
            }

            CopyDirectory(actualSource, gamePath);

            File.WriteAllText(Path.Combine(gamePath, "version.txt"), updateInfo.Version);

            File.Delete(updateFile);
            Directory.Delete(tempExtractPath, true);

            return true;
        }
        catch
        {
            return false;
        }
    }

    private void CopyDirectory(string sourceDir, string targetDir)
    {
        Directory.CreateDirectory(targetDir);

        foreach (var file in Directory.GetFiles(sourceDir))
        {
            string targetFilePath = Path.Combine(targetDir, Path.GetFileName(file));
            File.Copy(file, targetFilePath, true);
        }

        foreach (var directory in Directory.GetDirectories(sourceDir))
        {
            string targetDirPath = Path.Combine(targetDir, Path.GetFileName(directory));
            CopyDirectory(directory, targetDirPath);
        }
    }

    public void LaunchGame()
    {
        string gameExe = Path.Combine(gamePath, "ToyBattle.exe");

        if (File.Exists(gameExe))
        {
            System.Diagnostics.Process.Start(gameExe);
        }
    }

    public void UninstallGame()
    {
        try
        {
            if (Directory.Exists(gamePath))
            {
                Directory.Delete(gamePath, true);
            }
        }
        catch
        {
            // Error handling delegated
        }
    }
}