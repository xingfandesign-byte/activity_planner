# What is SpecStory?

[![Installs](https://img.shields.io/endpoint?url=https%3A%2F%2Fspecstory.com%2Fapi%2Fbadge%3Fstat%3Dinstalls&style=flat-square)](https://specstory.com/api/badge?stat=installs)
[![Active Users](https://img.shields.io/endpoint?url=https%3A%2F%2Fspecstory.com%2Fapi%2Fbadge%3Fstat%3DactiveUsers&style=flat-square)](https://specstory.com/api/badge?stat=activeUsers)
[![Sessions Saved](https://img.shields.io/endpoint?url=https%3A%2F%2Fspecstory.com%2Fapi%2Fbadge%3Fstat%3DsessionsSaved&style=flat-square)](https://specstory.com/api/badge?stat=sessionsSaved)
[![Rules Generated](https://img.shields.io/endpoint?url=https%3A%2F%2Fspecstory.com%2Fapi%2Fbadge%3Fstat%3DrulesGenerated&style=flat-square)](https://specstory.com/api/badge?stat=rulesGenerated)

[SpecStory](https://specstory.com) is a suite of **local-first extensions** that automatically captures your AI coding sessions as reusable git-friendly markdown. While Git tracks _what_ changed in your code, SpecStory helps capture _why_ it changed, preserving the reasoning and decision-making that drove the intent behind every line. Never lose AI chat history.

### ❗️Important Note

By default, installing from the Visual Studio Marketplace directly will install SpecStory into VS Code. To instead install SpecStory into Cursor, you must install directly from inside the extensions panel in Cursor (see details on our [documentation site](https://docs.specstory.com/specstory/introduction#cursor)).

## ✨ What the SpecStory extension does

### 📝 Automatic local capture

SpecStory automatically saves your AI conversations to `.specstory/history/` in your project directory. So your prompts stay with your code.

Toggle auto-save on/off in settings to match your workflow.

![Autosave_your_history](https://share.specstory.com/extension/autosave_your_history.gif)

### 🤖 Generate AI rules from your conversations

Transform your chat history into [Cursor Rules](https://docs.cursor.com/context/rules) or [Copilot Instructions](https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot). SpecStory uses your interaction data to create and maintain context files that keep your AI on track.

Customize the structure and SpecStory adapts to your preferences.

![Autogenerate_AI_rules](https://specstory.com/product_gifs/Derived-VSC.gif)

### 💾 Selective saving

Use Command Palette (CMD/Ctrl-Shift-P) → `SpecStory: Save AI Chat History` to manually save specific conversations when auto-save is off.

![Cherrypick_your_history](https://specstory.com/product_gifs/Save-VSC.gif)

### 🔗 Share conversations

Share your problem-solving process with teammates. Command Palette → `SpecStory: Share AI Chat History` creates anonymous shareable links to your conversations.

![Share your chat history](https://specstory.com/product_gifs/Share-VSC.gif)

## 🎮 Control panel

Access the SpecStory panel to manage histories, configure settings, and monitor auto-save status. Find it in the sidebar or via `View: Open View > SpecStory` in the command palette.

![SpecStory Control Panel](https://specstory.com/product_gifs/specstory-control-panel.png)

## 🛠️ For Developers

Enable `specstory.showDeveloperTools` in VS Code settings to access:

1. Debug logging in the SpecStory output channel
2. Cursor sqlite DB explorer in your Primary Sidebar with:

- **Search**: Command Palette → `SpecStory (Developer Tools): Search VS Code State` or click the magnifying glass icon
- **Refresh**: Command Palette → `SpecStory (Developer Tools): Refresh VS Code State` or use the refresh button
- **Copy values**: Hover over any value and click the copy icon

## ☁️ SpecStory Cloud

**SpecStory Cloud is a new progressive enhancement** of our local first extension suite that unifies all your AI conversations from Cursor, VS Code, Claude Code, and BearClaude into one searchable place.

### 🚀 Quick Start

#### For VS Code/Cursor users:

1. Sign up at [cloud.specstory.com](https://cloud.specstory.com)
2. Open Command Palette → `SpecStory: Open Cloud Sync Configuration`

You'll see this screen and then follow the authentication prompts to sync your first project:

![SpecStory Control Panel](https://specstory.com/product_gifs/specstory-cloud.png)

#### For Claude Code users:

1. Sign up at [cloud.specstory.com](https://cloud.specstory.com)
2. Authenticate: `specstory auth login`
3. Sync your conversations: `specstory sync`

### ✨ Why Cloud?

- **Search everywhere**: Full-text search across all your AI chats
- **Privacy first**: Nothing syncs without your explicit permission
- **All tools in one place**: Unify conversations from Cursor, VS Code, Claude Code, and more

[Full documentation →](https://docs.specstory.com/cloud/overview)

## ✨ We're always shipping something new

- Interested in a minimalist approach for turning markdown specs into software?
- Try our latest product for macOS at [bearclaude.com](https://bearclaude.com)

## 📚 Documentation & Community

- Find our docs chock full of use cases and a getting started guide to master your craft @ [docs.specstory.com](https://docs.specstory.com).
- Join our [slack community](https://join.slack.com/t/specstory/shared_invite/zt-2vq0274ck-MYS39rgOpDSmgfE1IeK9gg) to connect with other software composers!

## 🔮 Issue Reporting and Feature Requests

- Found a bug? Have a feature request? Please log it on our [issues page on GitHub](https://github.com/specstoryai/getspecstory/issues).
- For any other issue please email us at [support@specstory.com](mailto:support@specstory.com).

## 🔒 Privacy

SpecStory collects usage data to help improve the product. This can be disabled in the extension by unchecking `SpecStory: Help Us Improve` in your SpecStory extension settings.

This setting does not affect web analytics. For more information about what data we collect and how we use it, please see our [privacy policy](https://specstory.com/privacy) and [data privacy docs](https://docs.specstory.com/privacy) which provide detail by feature.
