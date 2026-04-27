# MCP Server License Notes

## Summary

The `mcp_server/` implementation in this project is a small custom server written for GrowthPilot Agent.

No large third-party MCP server codebase was copied into this repository.

## Reference Materials Reviewed

### 1. Official MCP Python SDK

Repository:

- `modelcontextprotocol/python-sdk`

Purpose of reference:

- understand the recommended `FastMCP` server structure
- confirm the minimal tool definition style
- confirm the standard server startup pattern

License:

- MIT

Reference:

- https://github.com/modelcontextprotocol/python-sdk

### 2. Official MCP Quickstart Resources

Repository:

- `modelcontextprotocol/quickstart-resources`

Purpose of reference:

- review the educational quickstart server layout and documentation style
- align the minimal server organization with official examples

License:

- MIT

Reference:

- https://github.com/modelcontextprotocol/quickstart-resources

### 3. Official MCP Reference Servers Repository

Repository:

- `modelcontextprotocol/servers`

Purpose of reference:

- review reference-server positioning and security framing
- confirm that reference examples are educational rather than production-ready

License:

- Apache License 2.0 for new contributions, with existing code under MIT, per the repository README/license notice

Reference:

- https://github.com/modelcontextprotocol/servers

## Copying Statement

- No large files or modules were copied from any third-party MCP server repository.
- No code was copied from `awesome-mcp-servers`.
- The implementation here was written from scratch for GrowthPilot Agent.
- Only general structure, naming patterns, and transport usage were informed by official MCP documentation and examples.

## Attribution Notes

Because this server uses the official MCP Python SDK API shape and references official examples for guidance, the project README and MCP README explicitly acknowledge those references.
