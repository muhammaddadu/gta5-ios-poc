# Integrated app status — 11 October 2026

The Glue5 runtime has been integrated into a local update of the existing GTA V
app. The old working app and IPA have not been replaced yet.

Implemented in the reproducible integration/build scripts:

- Pinned Glue5 revision and Rust compiler.
- Original app name/icon and the installed app's existing bundle ID.
- Legacy phone data/shader lookup and original Documents/userdata save location.
- Low-memory first-launch profile, approximately 640-line initial scene rendering,
  MetalFX spatial upscaling, frame pacing and in-game settings from Glue5.
- Analog virtual gamepad, real pad input/prompts/aim assist, native text entry,
  adaptive touch visibility and adjustable control size/opacity from Glue5.
- Original mobile refinements: minimum 44-point button hit areas, GTA V start title,
  human-readable storage status, and manifest-gated Play readiness.

Validated:

- Patched compiler/dependencies prepared and device ARM64 runtime compiled.
- Fourteen repository tests passed.
- Tests against actual modified Rust code passed for modern/legacy game layout,
  incomplete data rejection and minimum touch-target sizing.
- Existing phone userdata backed up: .local/upgrade-backups/userdata-before-glue5.
- Original working IPA remains .local/dist/export/GTA.ipa.

Current blocker: macOS is waiting for the owner's keychain approval for codesign.
The system signing prompt needs the Mac login password entered locally, not in a
chat or command. Installation and physical-device UX/gameplay checks have not yet
been completed for this update. Do not treat compiled code as improved gameplay
or measured performance. The previous phone validation applies to the old port.

Once signing finishes, rebuild/archive the final UX changes, verify the new IPA,
install over the same app ID, and test the start page/settings/touch/gamepad/scaling
and sustained performance. Do not uninstall the existing app or re-copy its assets
unless verification establishes that they are missing. See GLUE5_UPGRADE.md for
build, installation and rollback instructions.
