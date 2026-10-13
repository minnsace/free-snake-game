/* global Peer */
(() => {
  "use strict";
  const ui = Object.fromEntries(
    ["status", "presence", "alerts", "join", "leave", "mute", "play", "error"]
      .map(id => [id, document.getElementById(id)])
  );
  // All visitors to this deployed hostname share one room, including the iframe.
  const room = "free-snake-voice-v1-" + location.hostname.replace(/[^a-z0-9-]/gi, "-");
  let peer;
  let hub;
  let connection;
  let stream;
  let roster = [];
  let audioContext;
  let alertsEnabled = false;
  let joining = false;
  let lastHubMessage = 0;
  let lastAlert = 0;
  let lastAttempt = 0;
  const members = new Map();
  const calls = new Map();
  const audio = new Map();
  const report = message => { ui.error.textContent = message; };
  const voiceIds = () => roster.filter(member => member.voice).map(member => member.id);

  function update() {
    const count = voiceIds().length;
    ui.presence.textContent = count
      ? `${count} person${count === 1 ? "" : "s"} in voice chat${stream ? "" : " - join to answer!"}`
      : "Nobody in voice chat yet.";
    ui.join.disabled = !connection?.open || joining || !!stream;
    ui.join.hidden = !!stream;
    ui.leave.hidden = !stream;
    ui.mute.hidden = !stream;
  }

  function closeCall(id) {
    const call = calls.get(id);
    calls.delete(id);
    call?.close();
    const element = audio.get(id);
    if (element) {
      element.srcObject = null;
      element.remove();
      audio.delete(id);
    }
  }

  function registerCall(call) {
    const id = call.peer;
    calls.set(id, call);
    const timeout = setTimeout(() => {
      if (calls.get(id) === call && !audio.has(id)) {
        report("Voice connection timed out. Try leaving and rejoining; this network may need a different connection (Wi-Fi/mobile data).");
        closeCall(id);
      }
    }, 20000);
    call.on("stream", remote => {
      clearTimeout(timeout);
      if (calls.get(id) !== call) return;
      let element = audio.get(id);
      if (!element) {
        element = document.createElement("audio");
        element.autoplay = true;
        element.setAttribute("playsinline", "");
        document.body.append(element);
        audio.set(id, element);
      }
      element.srcObject = remote;
      element.play().catch(() => {
        ui.play.hidden = false;
        report("Your browser blocked incoming audio. Click Play incoming audio.");
      });
    });
    call.on("close", () => {
      clearTimeout(timeout);
      if (calls.get(id) === call) closeCall(id);
    });
    call.on("error", error => {
      clearTimeout(timeout);
      report(`Voice connection failed: ${error.message}`);
      if (calls.get(id) === call) closeCall(id);
    });
  }

  function syncCalls() {
    const ids = voiceIds();
    for (const id of calls.keys()) {
      if (!stream || !ids.includes(id)) closeCall(id);
    }
    if (!stream) return;
    for (const id of ids) {
      // One caller per pair prevents duplicate audio and offer collisions.
      if (peer.id < id && !calls.has(id)) registerCall(peer.call(id, stream));
    }
  }

  function broadcast() {
    const list = [...members.entries()].map(([id, member]) => ({ id, voice: member.voice }));
    for (const member of members.values()) {
      if (member.connection.open) member.connection.send({ type: "roster", members: list });
    }
  }

  function electHub() {
    if (hub || !peer?.open) return;
    hub = new Peer(room);
    const candidate = hub;
    candidate.on("connection", incoming => {
      incoming.on("open", () => {
        const previous = members.get(incoming.peer);
        previous?.connection.close();
        members.set(incoming.peer, { connection: incoming, voice: false, seen: Date.now() });
        broadcast();
      });
      incoming.on("data", data => {
        const member = members.get(incoming.peer);
        if (member?.connection !== incoming || data?.type !== "presence" || typeof data.voice !== "boolean") return;
        member.voice = data.voice;
        member.seen = Date.now();
        broadcast();
      });
      const remove = () => {
        if (members.get(incoming.peer)?.connection === incoming) {
          members.delete(incoming.peer);
          broadcast();
        }
      };
      incoming.on("close", remove);
      incoming.on("error", remove);
    });
    candidate.on("error", error => {
      if (error.type !== "unavailable-id") report(`Room service: ${error.message}`);
      candidate.destroy();
      if (hub === candidate) hub = undefined;
      members.clear();
    });
    candidate.on("disconnected", () => {
      report("Room host lost its signaling connection. Reconnecting...");
      candidate.destroy();
      if (hub === candidate) hub = undefined;
      members.clear();
    });
  }

  function sendPresence() {
    if (connection?.open) connection.send({ type: "presence", voice: !!stream });
  }

  function connect() {
    if (!peer?.open || connection || Date.now() - lastAttempt < 4000) return;
    lastAttempt = Date.now();
    electHub();
    const outgoing = peer.connect(room, { reliable: true });
    connection = outgoing;
    const timeout = setTimeout(() => {
      if (connection === outgoing && !outgoing.open) lost();
    }, 3500);
    function lost() {
      clearTimeout(timeout);
      if (connection !== outgoing) return;
      connection = undefined;
      outgoing.close();
      roster = [];
      syncCalls();
      ui.status.textContent = "Room connection lost. Retrying...";
      if (stream) report("Disconnected from the room. Your microphone is still enabled; voice will reconnect when the room returns.");
      update();
    }
    outgoing.on("open", () => {
      clearTimeout(timeout);
      lastHubMessage = Date.now();
      ui.status.textContent = stream ? "In voice chat - microphone enabled." : "Ready. Enable alerts, or join to talk.";
      sendPresence();
      update();
    });
    outgoing.on("data", data => {
      if (connection !== outgoing || data?.type !== "roster" || !Array.isArray(data.members)) return;
      if (!data.members.every(member => typeof member.id === "string" && typeof member.voice === "boolean")) return;
      lastHubMessage = Date.now();
      roster = data.members;
      syncCalls();
      update();
      ring();
    });
    outgoing.on("close", lost);
    outgoing.on("error", lost);
  }

  async function unlockAudio() {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) throw new Error("Sound alerts are not supported in this browser.");
    audioContext ||= new AudioContextClass();
    await audioContext.resume();
    if (audioContext.state !== "running") throw new Error("Sound is blocked. Click Enable alerts again.");
  }

  function beep() {
    for (const offset of [0, 0.3, 0.6]) {
      const oscillator = audioContext.createOscillator();
      const gain = audioContext.createGain();
      const time = audioContext.currentTime + offset;
      oscillator.frequency.value = 880;
      gain.gain.setValueAtTime(0, time);
      gain.gain.linearRampToValueAtTime(0.15, time + 0.02);
      gain.gain.linearRampToValueAtTime(0, time + 0.22);
      oscillator.connect(gain).connect(audioContext.destination);
      oscillator.start(time);
      oscillator.stop(time + 0.25);
    }
  }

  function ring() {
    if (!alertsEnabled || stream || !voiceIds().length || Date.now() - lastAlert < 5000) return;
    if (audioContext.state !== "running") {
      report("Alert audio is suspended. Click Enable alerts again and keep this tab open.");
      return;
    }
    lastAlert = Date.now();
    beep();
  }

  ui.alerts.onclick = async () => {
    try {
      await unlockAudio();
      alertsEnabled = true;
      ui.alerts.textContent = "Alerts enabled / test sound";
      report("");
      beep();
    } catch (error) { report(error.message); }
  };

  ui.join.onclick = async () => {
    joining = true;
    update();
    report("");
    try {
      if (!navigator.mediaDevices?.getUserMedia) throw new Error("Microphone requires HTTPS and a supported browser.");
      await unlockAudio();
      const captured = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
        video: false
      });
      if (!connection?.open) {
        captured.getTracks().forEach(track => track.stop());
        throw new Error("Room disconnected while asking for microphone access. Please try again.");
      }
      stream = captured;
      stream.getAudioTracks().forEach(track => track.onended = () => {
        leave();
        report("Microphone access ended. Join again to reconnect.");
      });
      ui.mute.textContent = "Mute microphone";
      ui.status.textContent = "In voice chat - microphone enabled.";
      sendPresence();
      syncCalls();
    } catch (error) { report(`Could not join: ${error.message}`); }
    finally { joining = false; update(); }
  };

  function leave() {
    const previous = stream;
    stream = undefined;
    previous?.getTracks().forEach(track => { track.onended = null; track.stop(); });
    for (const id of calls.keys()) closeCall(id);
    sendPresence();
    ui.status.textContent = connection?.open ? "Left voice chat. Listening for alerts." : "Disconnected. Retrying...";
    ui.play.hidden = true;
    update();
  }
  ui.leave.onclick = leave;
  ui.mute.onclick = () => {
    if (!stream) return;
    const enabled = !stream.getAudioTracks()[0].enabled;
    stream.getAudioTracks().forEach(track => { track.enabled = enabled; });
    ui.mute.textContent = enabled ? "Mute microphone" : "Unmute microphone";
    ui.status.textContent = enabled ? "In voice chat - microphone enabled." : "In voice chat - microphone muted.";
  };
  ui.play.onclick = async () => {
    try {
      await unlockAudio();
      await Promise.all([...audio.values()].map(element => element.play()));
      ui.play.hidden = true;
      report("");
    } catch (error) { report(`Audio is still blocked: ${error.message}`); }
  };

  if (typeof Peer === "undefined") {
    report("Voice service could not load. Check your internet connection and reload this page.");
    ui.status.textContent = "Voice chat unavailable.";
    return;
  }
  peer = new Peer();
  peer.on("open", connect);
  peer.on("call", call => {
    if (!stream || !voiceIds().includes(call.peer) || calls.has(call.peer)) {
      call.close();
      return;
    }
    registerCall(call);
    call.answer(stream);
  });
  peer.on("error", error => {
    if (error.type !== "peer-unavailable") report(`Voice service: ${error.message}`);
  });
  peer.on("disconnected", () => {
    connection?.close();
    ui.status.textContent = "Signaling disconnected. Reconnecting...";
    report("Voice service connection lost.");
    peer.reconnect();
  });
  setInterval(() => {
    const now = Date.now();
    for (const [id, member] of members) {
      if (now - member.seen > 15000) {
        members.delete(id);
        member.connection.close();
        broadcast();
      }
    }
    if (connection?.open && now - lastHubMessage > 15000) connection.close();
    connect();
    sendPresence();
    ring();
  }, 2000);
  window.addEventListener("pagehide", () => {
    leave();
    connection?.close();
    hub?.destroy();
    peer.destroy();
  });
})();
