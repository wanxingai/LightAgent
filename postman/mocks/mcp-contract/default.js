const http = require("http");

// Stateless Streamable HTTP contract used only for local SDK compatibility.
http.createServer(async (req, res) => {
  if (req.url !== "/mcp") {
    res.writeHead(501);
    return res.end();
  }
  if (req.method !== "POST") {
    res.writeHead(405, { Allow: "POST" });
    return res.end();
  }
  const message = req.body;
  if (!message || message.jsonrpc !== "2.0") {
    res.writeHead(400);
    return res.end();
  }
  if (message.id === undefined) {
    res.writeHead(202);
    return res.end();
  }
  let result;
  switch (message.method) {
    case "initialize":
      result = {
        protocolVersion: message.params.protocolVersion,
        capabilities: { tools: {} },
        serverInfo: { name: "lightagent-contract", version: "1.0" },
      };
      break;
    case "tools/list":
      result = { tools: [{
        name: "echo_header",
        description: "Echo a non-secret test header",
        inputSchema: { type: "object", properties: {} },
      }] };
      break;
    case "tools/call":
      if (message.params.name !== "echo_header") {
        res.writeHead(501);
        return res.end();
      }
      result = {
        content: [{ type: "text", text: req.headers["x-lightagent-test"] || "missing" }],
        isError: false,
      };
      break;
    default:
      res.writeHead(501);
      return res.end();
  }
  res.writeHead(200, { "Content-Type": "application/json" });
  res.end(JSON.stringify({ jsonrpc: "2.0", id: message.id, result }));
}).listen(process.env.PORT);
