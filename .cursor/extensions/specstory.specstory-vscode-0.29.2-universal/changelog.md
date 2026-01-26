# Changelog

All notable changes to the SpecStory extension are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.29.2] - 2026-01-16

· Bugfix: Disable reporting of errors if the user has opted out of telemetry.

## [0.29.1] - 2026-01-13

· Bugfix: Fix an issue with the VSCode storage service not returning any composer refs if the composer data is not present.

## [0.29.0] - 2026-01-13

· Update AI Rules generation endpoint

· Refactored project architecture and simplified build tooling

## [0.28.1] - 2025-12-30

· Enhanced network security hardening

## [0.28.0] - 2025-12-23

· Added support for Cursor's edit_file_v2 tool

## [0.27.3] - 2025-12-19

· Performance: Optimized database queries for faster conversation loading.

## [0.27.2] - 2025-12-15

· Bugfix: Resolved an issue in Visual Studio Code conversations related to string trimming.

## [0.27.1] - 2025-12-10

· Improved error reporting from bubble handlers

· Enhanced grep and list directory tool handlers

· Added support for Cursor's read_file_v2 and run_terminal_command_v2 tools

## [0.27.0] - 2025-12-02

· Better support for Visual Studio Code conversations

## [0.26.1] - 2025-11-25

· Open the Cloud Sync configuration panel when sync is turned on via URI parameter.

## [0.26.0] - 2025-11-21

· Install, authenticate and sync your sessions with one click from cloud.specstory.com

## [0.25.1] - 2025-11-19

· Minor updates to markdown generation format

## [0.25.0] - 2025-11-13

· New sharing experience: use the Cloud UI to share your chats.

## [0.24.3] - 2025-11-12

· Bugfix: Add support for authentication redirects in minor VS Code forks, including VSCodium and Code-OSS.

· Bugfix: Prevent overwriting markdown files during auto-save when conversation names collide.

· Improve performance of Cloud Sync by reducing the number of requests to the server.

## [0.24.2] - 2025-11-05

· UX improvements to Cloud Sync and Control Panel

## [0.24.1] - 2025-11-03

· Bugfix: Force encoding of the session body to UTF-8 to avoid issues on the server side.

## [0.24.0] - 2025-10-31

· Add support for the new tool and thinking message layout

· Display agent mode and model for each exchange (Cursor only, for now)

· Include user email in the project identity

· Initialize project identity if at least one service is enabled: Cloud Sync, Auto-Save, or Derived Rules

· Halloween release

## [0.23.0] - 2025-10-13

· Add support for Ripgrep tool

## [0.22.0] - 2025-10-06

· Add support for Write tool

## [0.21.0] - 2025-10-01

· Add support for Apply Patch tool

· Add support for Grep tool

· Add support for Glob File Search tool

· Add support for Read Lints tool

· New tools discovery

## [0.20.0] - 2025-09-24

· Add editor and agent model information to exported markdown files. Note: Agent model reflects only the most recently used model, as composer objects do not store historical model usage.

· Fix read file tool output formatting

· Add support for MultiEdit tool handler

· Bugfix: Fix infinite loop in project identity initialization that occurred when .project.json files were manually copied and edited

## [0.19.2] - 2025-09-10

· Improved the SpecStory Cloud sync process for the first time sync of projects with a large number of chats.

## [0.19.1] - 2025-09-07

· Fix an issue with SpecStory Cloud login

## [0.19.0] - 2025-09-07

· Search across all your AI Chat history with the [SpecStory Cloud](https://cloud.specstory.com) web app

· Automatically synchronizes your AI chat sessions with SpecStory Cloud when you are logged in and SpecStory Cloud sync is enabled for the current project.

· New setting, `specstory.cloudSync.enabled`, to turn on or off cloud sync for new projects. It defaults to `ask` to prompt you for new projects. Other options are `always` to turn on cloud sync for new projects and `never` to turn off cloud sync for new projects.

· Note: In this initial release of SpecStory Cloud, the default "ask" option is passive and requires you to manually turn on SpecStory Cloud sync for new projects.

· New SpecStory Cloud Sync panel to show the project's SpecStory Cloud settings and status. Available in the command palette as `SpecStory: Open Cloud Sync Configuration` or by clicking the "Cloud Sync" item in the SpecStory control panel.

## [0.18.0] - 2025-09-02

· Added a timestamp to user prompt header when saving markdown from Cursor chats. This timestamp respects the `SpecStory: Coordinated Universal Time (UTC)` setting for UTC or local time. [issues/104](https://github.com/specstoryai/getspecstory/issues/37)

· In the SpecStory control panel show the last auto-save time in local time, rather than in Coordinated Universal Time (UTC).

· Debounced the auto-save to reduce the number of times the database is checked for changes.

## [0.17.1] - 2025-07-31

· Bugfix: Perform initial composers scan on startup rather than waiting for the first polling interval.

· Bugfix: Add VS Code Insiders authentication link to the preferences page.

· Migrate the SpecStory control panel UI to React for improved maintainability and user experience.

## [0.17.0] - 2025-07-24

· Added support for MCP tool calls. [community issue](https://specstory.slack.com/archives/C079CTL1XSN/p1753143266218809)

· Bugfix: make sure cursor indexing ignores the specstory directory.

## [0.16.0] - 2025-07-23

· Updated for Cursor 1.2: Added support for todo items and memory updates. [See Cursor changelog](https://cursor.com/en/changelog)

· Added support for search-and-replace and notebook edit tools. [issues/87](https://github.com/specstoryai/getspecstory/issues/87)

· Improved the layout of file edit diffs in markdown.

· Now displays the list of pull requests referenced during a codebase search, when available.

· Fixed an issue where markdown filenames did not use the correct day number.

· Fixed an issue where code blocks for changed files were not visible in markdown output.

· Fixed an issue where the `.specstory` directory was not added to `.cursorindexignore`. [issues/84](https://github.com/specstoryai/getspecstory/issues/84)

## [0.15.0] - 2025-07-10

· Add support for authenticating on VS Code - Insiders. [issues/79](https://github.com/specstoryai/getspecstory/issues/79)

· Do not show the Storage Composer tree in the SpecStory Control Panel (under dev tools) in case it's too large to load. [issues/77](https://github.com/specstoryai/getspecstory/issues/77)

· Safe fail in case some composers are too large to load. [issues/75](https://github.com/specstoryai/getspecstory/issues/75)

## [0.14.0] - 2025-07-08

· Adjust the conditions we use when saving conversations to ensure saves occur after initial save. [issues/82](https://github.com/specstoryai/getspecstory/issues/82)

· Adding a handler for the new `create_diagram` tool in Cursor. [issues/78](https://github.com/specstoryai/getspecstory/issues/78)

## [0.13.0] - 2025-06-27

· Ensure we are capturing the new thinking message structure generated by Cursor in our markdown output. [issues/55](https://github.com/specstoryai/getspecstory/issues/55)

· Add a new setting in the SpecStory settings view for toggling between saving files with a local time or UTC TZ format. [issues/49](https://github.com/specstoryai/getspecstory/issues/49)

Defects

· Ensure we properly notify the user when they are trying to utilize SpecStory in a window without a workspace. [issues/50](https://github.com/specstoryai/getspecstory/issues/50)

· Avoid rewriting the `.what-is-this.md` file, as well as adding a content check. [issues/65](https://github.com/specstoryai/getspecstory/issues/65)

## [0.12.1] - 2025-05-26

Defects

· Only write `.gitignore` entries in `.specstory` directory, not the root of the project [issues/59](https://github.com/specstoryai/getspecstory/issues/59).

· Use Windows-style end of line (EOL) for saves, auto-saves, and auto-generated files [issues/61](https://github.com/specstoryai/getspecstory/issues/61).

· Modification to how we monitor for changes in Visual Studio Code to more proactively update chat histories.

· Ensure we are properly referencing the chat log ID in Visual Studio Code when checking if we need to re-save a chat.

## [0.12.0] - 2025-05-08

· Beta support for saving chat histories in [Visual Studio Code (VSCode) Insiders](https://code.visualstudio.com/insiders/). Support for auto-saving as well as manual saving.

Defects

· Missing agent responses in Agent mode when using VSCode. This is only resolved for the `SpecStory: Save AI Chat History` and for auto-save, and may be delayed waiting for VSCode to generate the agent response JSON. Not yet resolved for the `SpecStory: Share AI Chat History` command.

## [0.11.4] - 2025-05-05

Defects

· A more comprehensive fix for Cursor crashes due to failure of Cursor to obtain a DB lock [issues/54](https://github.com/specstoryai/getspecstory/issues/54) which now also addresses [issues/58](https://github.com/specstoryai/getspecstory/issues/58).

· Fix for the Auto-save indicator in the SpecStory control panel UI sometimes indicating "Off" when it's "On".

## [0.11.3] - 2025-05-01

Defects

· Remove the pre-emptive auto-save run, which was done on SpecStory extension activation, to avoid crashing Cursor on startup in some cases of large DBs (100's of MBs+), lots of Cursor windows re-opening, and limited computer resources [issues/54](https://github.com/specstoryai/getspecstory/issues/54). Thanks to Chris from down under 🇦🇺 for help in replicating the issue so we could solve it.

## [0.11.2] - 2025-04-29

· Updated the `what-is-this.md` file content to account for Visual Studio Code support.

· Updated the `what-is-this.md` file to explain the new `.specstory/.project.json` file which is present if you are using SpecStory AI rules generation.

· `.specstory/ai_rules_backups` is automatically added to `.gitignore` if you are using AI rules generation.

· `.specstory/.project.json` is automatically added to `.gitignore` if you are using AI rules generation.

## [0.11.1] - 2025-04-25

· Minor changes to command palette command names. Now `SpecStory: Save AI Chat History` and `SpecStory: Share AI Chat History`.

## [0.11.0] - 2025-04-25

· Beta support for saving chat histories in Visual Studio Code (VSCode), including [Copilot agent mode](https://code.visualstudio.com/blogs/2025/02/24/introducing-copilot-agent-mode). Support for auto-saving as well as manual saving.

· Beta support for sharing chat histories in VSCode to `share.specstory.com`.

· Automated [Copilot instructions](https://code.visualstudio.com/docs/copilot/copilot-customization) generation based on your saved chat history.

· Renaming and automatic migration of SpecStory settings. Now `specstory.derivedRules.enabled` and `specstory.derivedRules.headers` instead of `specstory.derivedCursorRules.enabled` and `specstory.derivedCursorRules.headers`.

## [0.10.1] - 2025-04-18

· The Cursor gods giveth, and the Cursor gods taketh away. And sometimes, like today, the Cursor gods unleash a biblical hellfire of crap so fierce that Moses himself weeps! A Good Friday indeed. Fear not, my fellow Cursor disciples! We've laid hands on SpecStory, making it compatible with whatever demonic possession hath taken over Cursor 0.49.x. The SpecStory team spent 40 days and 40 nights wandering in the debugging wilderness to deliver this miracle. (Okay, it was just one day, but it felt like 40.) Some here have taken to calling this update the New Testament... but we're just going to call it 0.10.1 because... you know... semantic versioning. Rejoice, repent, and carry on!

## [0.10.0] - 2025-04-10

· Adjusted Cursor rules derivation prompt to be more conservative in what it considers to be rule-worthy.

· Removed project structure content from Cursor Rules derivation requests.

· Debounced Cursor Rules derivation to reduce derivation requests.

· Added `./specstory` directory to `.cursorindexingignore` when auto-save is enabled so Cursor will ignore history files unless they are referenced manually.

## [0.9.1] - 2025-03-14

Defects

· Fixed auto-save and Cursor rules generation not working on remote SSH workspaces [issues/44](https://github.com/specstoryai/getspecstory/issues/44)

## [0.9.0] - 2025-03-13

· Added tool support for rendering agent use of the tools: `read_file`, `web_search`, `diff_history`, and `fetch_rules`.

· Include raw output from Cursor when the agent uses tools for which SpecStory doesn't have dedicated renderings.

· Added rendering of agent thought from thinking models (e.g. `claude-3.7-sonnet-thinking`, `o1`, `o3-mini`, etc.).

· Include Cursor captured human edits in code diff renderings.

· Made the date format consistent as `YYYY-MM-DD` throughout to avoid ambiguity [issues/34](https://github.com/specstoryai/getspecstory/issues/34).

· Moved the `what-is-this.md` file location from `.specstory/history` to just `.specstory` to account for the new `.specstory/cursor_rules_backups` directory.

Defects

· Removed the blank `_****_` content that was improperly included in the markdown files between parts of the agent response.

· Fixed a race condition in markdown rendering on incomplete Cursor composer data.

## [0.8.0] - 2025-03-03

· Introduced story mode for SpecStory shares. This allows you to insert markdown blocks anywhere around your AI interactions, creating a narrative flow that highlights critical moments and decisions, telling the story behind your development session, and making your thought process transparent to others.

· Added a floating table of contents to SpecStory shares, based on all the composer sessions in the share, and any markdown title headers.

· Improved layout and styling for shares on the web.

· Improved the handling of backup files in the experimental `.cursor/rules` file generation so they don't just grow in number without bound. The most recent 50 backup files are retained.

## [0.7.0] - 2025-03-03

· EXPERIMENTAL: SpecStory can now automatically generate and maintain a `.cursor/rules` file based on your chat and composer history. (Note that this feature is experimental and may be enhanced, modified or disabled in the future.)

· Use of the SpecStory Cursor rules generation requires you to create and sign in to a SpecStory account.

· New setting, `specstory.derivedCursorRules.enabled`, to turn the automatic cursor rules generation on or off. It's off by default.

· New setting, `specstory.derivedCursorRules.headers`, to guide the format and output of cursor rules generation. A set of standard headers, based on best practices, is provided by default.

· Each time the `.cursor/rules/derived-cursor-rules.mdc` is automatically update, the prior version is backed up to `.specstory/cursor_rules_backups`.

· `.specstory/cursor_rules_backups` is automatically added to `.gitignore` if you are using SpecStory Cursor rules generation.

## [0.6.2] - 2025-02-26

· Normalized some of the UI language around "Share" and "Save".

· Removed opening the "No composers selected" tab when canceling the save.

Defects

· Fixed SpecStory when using Cursor with a dedicated workspace file, specifically on Windows [issues/31](https://github.com/specstoryai/getspecstory/issues/31), [issues/4](https://github.com/specstoryai/getspecstory/issues/4).

## [0.6.1] - 2025-02-23

Defects

· Update the timestamp in the auto-save file name to not use a colon, for compatibility with Windows file systems [issues/30](https://github.com/specstoryai/getspecstory/issues/30).

## [0.6.0] - 2025-02-22

· Use the timestamp from when the Composer or Chat was created in the name of the auto-save file name so that auto-saved files are in chronological order in the filesystem [issues/29](https://github.com/specstoryai/getspecstory/issues/29). NOTE: This update renames any existing auto-save files so that they have a timestamp.

· Added an option to include a GitHub repository link in shares on the web.

· Added the ability to include embed videos (iFrame tags) from Tella, YouTube and Vimeo in the project description of shares on the web.

· Improved layout and styling for shares on the web.

## [0.5.0] - 2025-02-03

· Include output from Cursor Composer agent tools in markdown saves and auto-saves, and in web shares. These previously resulted in blank _**Assistant**_ blocks in the markdown.

· Improved layout and styling for shares on the web.

## [0.4.2] - 2025-01-22

Defects

· Fix issue with not seeing the correct Composers and Chats when opening the workspace from a workspace file rather than from a directory. Thanks to Geoff R. for reporting the issue in our Slack community, and for joining us on a call all the way from Australia 🇦🇺 to help us better understand the issue.

## [0.4.1] - 2025-01-20

· Improved layout and styling for shares on the web.

Defects

· Fix broken auto-save when workspace is remote on WSL, SSH, or Dev Container, [issues/19](https://github.com/specstoryai/getspecstory/issues/19) and [issues/23](https://github.com/specstoryai/getspecstory/issues/23).

## [0.4.0] - 2025-01-16

· Improved layout and styling for shares on the web.

· Action to make it easy to copy the user prompt from shares on the web, in case the reader wants to try out the prompt.

· The SpecStory cursor extension now has a UI that includes:

    · Save and share functionality

    · Access the extension settings

    · Real-time auto-save status

    · Extension version display, with link to this change log

Defects

· The 25MB limit on shares has now been removed, though very large shares are likely to time-out during rendering. We're working on this.

## [0.3.3] - 2025-01-15

Defects

· Fix reintroduced defect with broken composer and chat history loading issue that occurred when the _current workspace_ path has been re-used by a different workspace. For example, if you deleted a workspace and then created a new one with the same name, the new workspace might not have loaded the composer and chat history from the newest workspace.

## [0.3.2] - 2025-01-14

· Improve styling and usability of SpecStory Share web application.

· Display file path and name, when present, in the SpecStory Share web application.

· Fix the display of ordered and unordered lists in the SpecStory Share web application.

· Database optimization to improve performance and reduce memory usage when saving, sharing, or auto saving.

Defects

· Fix rendering of fenced code blocks in the SpecStory Share web application to make sure they're properly formatted and styled.

· The composer name is used as the filename for auto-saved markdown files. If the name contains unicode special characters, it was causing an error. Now those are handled properly.

## [0.3.1] - 2025-01-12

Defects

· The composer name is used as the filename for auto-saved markdown files. If the name is too long for a filename it was causing an error. Now it's truncated in the middle.

## [0.3.0] - 2025-01-10

· SpecStory now auto-saves your chat and composer history to `.specstory`. Auto-save works on a markdown file per chat/composer basis.

· New setting, `specstory.autoSave.enabled`, to turn off auto-save, for folks that prefer only manual save from the command palette.

· Remove the extra markdown preview window after saving, this proved to be confusing.

· After sharing to `share.specstory.com`, you get a cookie that identifies you as the sharer, and enables
you to edit the share:

    · The sharer can add a description with markdown and image support.

    · The sharer can delete individual chats and composers from the share.

Defects

· Fix broken composer and chat history loading issue that occurred when the _current workspace_ path has been re-used by a different workspace. For example, if you deleted a workspace and then created a new one with the same name, the new workspace might not have loaded the composer and chat history from the newest workspace.

· Fix [issues/11](https://github.com/specstoryai/getspecstory/issues/11), "Failed to read composer data from global storage: Error: database disk image is malformed". This happened when reading the Cursor SQLite database file while Cursor was writing to it. The extension now retries loading the database with a delay of 500ms between each attempt.

## [0.2.7] - 2025-01-07

Defects

· Fixes an issue when parsing Cursor JSON data during markdown rendering, [issues/14](https://github.com/specstoryai/getspecstory/issues/14).

## [0.2.6] - 2025-01-03

Defects

· Fix missing AI interactions when using Cursor Composer in Agent mode. This is just basic support for now. We'll be improving this to show code diffs, terminal output, linting results, and more. The goal is to better match how the Agent mode AI interactions are displayed in Cursor.

## [0.2.5] - 2025-01-02

· Added debug logging to the extension which can be enabled via `SpecStory: Show Developer Tools`. This goes to the "SpecStory" Output Channel in Cursor.

Defects

· Fix broken workspace loading issue that occurred when the _current workspace_ has a non-traditional path, such as a devcontainer, WSL, or a remote workspace, [issues/4](https://github.com/specstoryai/getspecstory/issues/4).

## [0.2.4] - 2024-12-31

· New setting, `specstory.helpUsImprove`, to allow folks to opt out of product analytics

· Added emojis to the `SpecStory: 📝 Save Composer and Chat History` and `SpecStory: ☁️ Share Composer and Chat History` commands

Defects

· Fix broken workspace loading issue that occurred when _any workspace_ had a non-traditional path, such as a devcontainer, [issues/4](https://github.com/specstoryai/getspecstory/issues/4). Thanks, Nick! 🕺🏻

## [0.2.3] - 2024-12-18

Chat / Composer Selection

· Select the specific composers or chats you want to save to a local markdown file.

· Select the specific composers or chats you want to share to share.specstory.com.

Defects

· Document that installing directly from the VSC Marketplace installs the extension into VSC, not into Cursor, [issues/8](https://github.com/specstoryai/getspecstory/issues/8)

· Fix broken workspace loading on Windows, [issues/4](https://github.com/specstoryai/getspecstory/issues/4)

## [0.1.2] - 2024-12-16

Update some documentation links.

## [0.1.1] - 2024-12-16

Clarify that SpecStory is an extension for the [Cursor](https://www.cursor.com/) fork of Visual Studio Code.

## [0.1.0] - 2024-12-14

### Initial Release

Cursor Extension

· Save composer and chat history log to a local markdown file

· Share composer and chat history log to the share.specstory.com web application

· Settings: Manage via VS Code Settings → User → Extensions → SpecStory

· Settings: Debug mode to browse Cursor Chat DB (opens VS Code State in your Primary Sidebar’s Tree View)

The share.specstory.com web application

· Get a unique URL to share

· Web rendered and formatted version of the composer and chat history

· Expand and collapse the composer and chat history

· Copy the composer and chat history log from the web to your clipboard in Markdown

## [Unreleased]

> “A story has no beginning or end: arbitrarily one chooses that moment of experience from which to look back or from which to look ahead.”
> Graham Greene, The End of the Affair
