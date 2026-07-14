#!/usr/bin/env node

const url = process.env.TRAFIKU_SOCKET_URL
  ?? "wss://tu.appbites.dev/ws/socket.io/?EIO=4&transport=websocket";
const timeoutMs = Number(process.env.TRAFIKU_SOCKET_TIMEOUT_MS ?? 20000);
const socket = new WebSocket(url);
let finished = false;

function finish(code, output) {
  if (finished) return;
  finished = true;
  clearTimeout(timer);
  if (output) console.log(JSON.stringify(output, null, 2));
  socket.close();
  process.exitCode = code;
}

const timer = setTimeout(
  () => finish(1, { error: `no bus_update received within ${timeoutMs} ms` }),
  timeoutMs,
);

socket.addEventListener("message", ({ data }) => {
  if (typeof data !== "string") return;
  if (data.startsWith("0")) {
    socket.send("40");
    return;
  }
  if (data.startsWith("2")) {
    socket.send(`3${data.slice(1)}`);
    return;
  }
  if (!data.startsWith("42")) return;
  const [event, payload] = JSON.parse(data.slice(2));
  if (event !== "bus_update") return;
  const first = Array.isArray(payload) ? payload[0] : null;
  finish(0, {
    event,
    buses: Array.isArray(payload) ? payload.length : null,
    sample: first && {
      _id: first._id,
      number: first.number,
      name: first.name,
      line: first.line,
      coordinates: first.geometry?.coordinates,
      heading: first.heading,
      visible: first.is_visible,
    },
  });
});

socket.addEventListener("error", () => finish(1, { error: "WebSocket connection failed" }));
