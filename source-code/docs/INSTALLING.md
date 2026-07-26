# Installing

### [⬇️ Download the installer](https://github.com/victorhuggomed2006-ux/YoutubeDownloader/raw/main/YouTubeDownloader-1.3.0-Setup.msi)

*96 MB · Windows 10 or 11, 64-bit*

The installer also lives on the
[releases page](https://github.com/victorhuggomed2006-ux/YoutubeDownloader/releases/latest),
which is where previous versions are kept.

## Steps

1. Download the file
2. Double-click it
3. Choose whether you want a Desktop shortcut
4. Finish

That is it. No administrator prompt, and no Python, FFmpeg or anything else to
install — it is all inside the installer.

## Where the program goes

Into `%LOCALAPPDATA%\Programs\YouTube Downloader`, the folder Windows reserves
for single-user programs. It is the same place Chrome, Discord and Spotify
install into.

It is not `C:\Program Files` for a technical reason: writing there requires
administrator rights, with no exceptions. An installer that asks for nothing
is, necessarily, one that does not write to Program Files.

## Uninstalling

**Settings → Apps → Installed apps**, find *YouTube Downloader* and click
Uninstall. No special permission needed.

Your settings and history live in `%APPDATA%\YouTubeDownloader` and are not
removed with it — delete that folder by hand if you want a clean slate.

## The Windows warning

The installer is not code-signed yet, so SmartScreen shows *"Windows protected
your PC"*. Click **More info**, then **Run anyway**.

This happens with any unsigned program, and the certificate that removes the
warning costs a few hundred dollars a year. The source is open in this
repository and you can build it yourself if you would rather not trust the
binary. The plan to fix this is in [CODE-SIGNING.md](CODE-SIGNING.md).

## Silent installation

```powershell
msiexec /i YouTubeDownloader-1.3.0-Setup.msi /qn
```

The Desktop shortcut is created unless you say otherwise:

```powershell
msiexec /i YouTubeDownloader-1.3.0-Setup.msi /qn INSTALLDESKTOPSHORTCUT=0
```

The package is per-user and UAC-compliant, which means Windows ignores
`ALLUSERS` and `MSIINSTALLPERUSER`: there is no combination of properties that
installs it machine-wide. Deploying to every user of a machine means running it
once per profile.
