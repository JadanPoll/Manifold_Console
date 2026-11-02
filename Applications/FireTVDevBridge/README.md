# Fire TV Dev Bridge

Native, remote-friendly Fire OS development bridge. First target: **Fire OS 7.7.1.7 (Android API 28)**. Located in Manifold Console as a standalone app; no changes to the other applications.

## Current working contract

- D-pad/remote-accessible launcher activity; local keycode event monitor.
- Explicit release lookup (never automatic background polling).
- Fetch APK only from this repository's named GitHub Release asset.
- Check the release's SHA-256 against the actual downloaded APK before opening the Android installer.
- Require the Fire TV's **Install unknown apps** grant and **system install confirmation**.
- User-triggered sharing of local device info and recent *key codes*; no upload endpoint, data collection, or remote commands.

## Bootstrap

1. On Fire TV, install **Downloader by AFTVnews** from the Amazon Appstore.
2. Enable Settings > My Fire TV > Developer Options > Install Unknown Apps > Downloader.
3. Once the [first CI build](https://github.com/JadanPoll/Manifold_Console/actions/workflows/firetv-dev-bridge.yml) has published, open the [rolling bridge APK](https://github.com/JadanPoll/Manifold_Console/releases/download/firetv-dev-bridge-latest/firetv-dev-bridge.apk) in Downloader, and confirm installation.
4. Launch **Fire TV Dev Bridge**; select CHECK LATEST GITHUB BUILD. To update, grant the *bridge* permission in Install Unknown Apps and select DOWNLOAD & INSTALL.

### Build

GitHub Actions builds on changes to this folder and publishes a rolling development release. For local Linux builds with Android SDK 35 and Gradle 8.10.2:

```sh
base64 -d signing/lab.keystore.base64 > signing/lab.keystore
gradle :app:assembleRelease
```

Java 17 required. Workflow versionCode uses monotonically increasing GITHUB_RUN_NUMBER.

### Security / constraints

**The checked-in signing credential is intentionally PUBLIC and LAB-ONLY.** It is not a secure Android app identity. Do not add account credentials, personal files, privileged permissions, automatic unattended installs, or production update channels to an app signed this way. Replace it with a protected, privately held signing key before production, using an explicit key migration plan (a new package name or uninstall/reinstall may be needed).

The helper cannot install apps silently, cannot see every system log, and cannot implement global key debouncing without additional privileged capabilities. It only observes keys inside its own Activity. The GitHub release uses a stable tag for an easy, repeatable URL; GitHub Actions artifacts also remain available per run.

## Next phases

1. Establish an installed, updateable baseline on the target Fire TV; report device/model and remote behavior.
2. Add an explicit, authenticated diagnostic-upload channel and a manifest of lab applications, *after* designing authorization and consent.
3. Add optional ADB-based debugging with separate credentials and least-privilege access.
4. Create an input normalization test suite for Firefly that distinguishes application-local event handling from global OS interception.
