---
description: Build a zipped appPackage with template variables resolved (atk package)
allowed-tools: ["Bash", "Read", "Glob"]
argument-hint: "[path_to_appPackage] [--env dev]"
---

# Toolkit Package — Build App Package Zip

Build a zipped appPackage with all `${{VAR}}` template variables resolved from the environment file.

## Steps

1. **Locate the appPackage**: Use the argument path if provided, otherwise look for `appPackage/` or `appPackage.dev/` in the current directory. If multiple found, ask which to package.

2. **Determine the environment**: Use `--env` argument if provided. Otherwise infer from the folder name:
   - `appPackage/` → `local`
   - `appPackage.dev/` → `dev`
   - `appPackage.<name>/` → `<name>`

3. **Find the project root**: The project root is the parent directory of the appPackage folder (where `m365agents.yml` or `env/` lives).

4. **Verify env file exists**: Check that `env/.env.<env>` exists in the project root. If not, warn that template variables won't resolve.

5. **Create output directory** if needed:
   ```bash
   mkdir -p <appPackage_path>/build
   ```

6. **Run atk package**:
   ```bash
   atk package --env <env> --manifest-file <appPackage_path>/manifest.json --output-package-file <appPackage_path>/build/appPackage.<env>.zip --folder <project_root> -i false
   ```

7. **Verify the build**:
   - List the zip contents to confirm all files are included
   - Check that `manifest.json` inside the zip has the `id` resolved (not `${{TEAMS_APP_ID}}`)

8. **Report**: Show the output path and file count.

## Examples

```bash
# Package appPackage.dev with dev env
/copilot-declarative-agent:toolkit-package appPackage.dev --env dev

# Package appPackage with local env
/copilot-declarative-agent:toolkit-package appPackage

# Package with explicit path
/copilot-declarative-agent:toolkit-package /home/user/project/agents/appPackage.dev
```
