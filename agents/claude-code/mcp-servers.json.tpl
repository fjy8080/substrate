{
  "_comment": "Claude Code 全局 MCP 服务器模板（已脱敏）。恢复时不要直接覆盖 ~/.claude.json（它是含机器状态的大文件），用 install.sh 的 --merge-mcp 或手动 jq 合并 mcpServers 节点，并把 <ZAI_BEARER_TOKEN>/<ZAI_API_KEY> 替换为真实凭据（清单见 docs/secrets-checklist.md）。",
  "mcpServers": {
    "web-reader": {
      "type": "http",
      "url": "https://api.z.ai/api/mcp/web_reader/mcp",
      "headers": {
        "Authorization": "Bearer <ZAI_BEARER_TOKEN>"
      }
    },
    "web-search-prime": {
      "type": "http",
      "url": "https://api.z.ai/api/mcp/web_search_prime/mcp",
      "headers": {
        "Authorization": "Bearer <ZAI_BEARER_TOKEN>"
      }
    },
    "zread": {
      "type": "http",
      "url": "https://api.z.ai/api/mcp/zread/mcp",
      "headers": {
        "Authorization": "Bearer <ZAI_BEARER_TOKEN>"
      }
    },
    "zai-mcp-server": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@z_ai/mcp-server"],
      "env": {
        "Z_AI_MODE": "ZHIPU",
        "Z_AI_API_KEY": "<ZAI_API_KEY>"
      }
    }
  }
}
