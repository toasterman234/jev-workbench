# Jev Workbench

A single-user, local browser workbench for macOS. The user publishes inputs, independent judgment questions, review rules, and output mappings as immutable function versions, then calls them over scoped HTTP, MCP, or Pi. Management is local; inference runs in the TypeSafe cloud. The success path is configure → real preview → publish → grant → call. The base contract is specs/v1/spec.md; the confirmed single-page layout and delete behaviour are in specs/single-page/spec.md.

The interface follows DropAgent's visual language (specs/dropagent-visual/spec.md): a directory rail on the left, the current function on the right, and Noul / Choice / Score offered directly at the point of creation. English and 中文 are both supported, dark and light both ship. When the user has no TypeSafe key, the product uses an explicit, separate demo mode and never presents a simulated success as real inference.
