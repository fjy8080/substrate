{
  "_comment": "Claude Code 全局 MCP 服务器模板。填入 <ZAI_*> 凭据后用 install.sh --merge-mcp 合并进 ~/.claude.json（~/.claude.json 含机器状态，不要整文件覆盖）。",
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
