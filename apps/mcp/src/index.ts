import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { credentials, callBackend } from "./client";
const path = process.argv[process.argv.indexOf("--credentials-file") + 1];
if (!process.argv.includes("--credentials-file") || !path)
  throw new Error("Pass --credentials-file /absolute/file.json");
const c = credentials(path),
  server = new McpServer({ name: "jev-workbench", version: "0.1.0" });
const schemas = {
  jev_list_functions: {},
  jev_describe_function: {
    key: z.string(),
    version: z.number().int().positive().optional(),
  },
  jev_invoke: {
    key: z.string(),
    version: z.number().int().positive().optional(),
    input: z.record(z.unknown()),
  },
};
for (const [name, inputSchema] of Object.entries(schemas)) {
  server.registerTool(
    name,
    {
      description:
        name === "jev_invoke"
          ? "Call a granted judgment function. Inference runs in the TypeSafe cloud and may be billed. needs_review means the judgment completed and needs a human look; it is never permission to act automatically."
          : name === "jev_list_functions"
            ? "List the judgment functions and versions this credential may call."
            : "Read a judgment function's input, output, and usage notes.",
      inputSchema,
    },
    async (args: any, extra: any) => {
      const r = await callBackend(c, name, args, extra.signal);
      const data = Array.isArray(r.data) ? { functions: r.data } : r.data;
      return {
        content: [{ type: "text" as const, text: JSON.stringify(data) }],
        structuredContent: data,
        isError: r.error,
      };
    },
  );
}
await server.connect(new StdioServerTransport());
